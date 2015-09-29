#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# Copyright (C) 2013  Jamie Duncan (jamie.e.duncan@gmail.com)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# File Name : newrelic.py
# Creation Date : 11-06-2013
# Created By : Jamie Duncan
# Last Modified : Thu 12 Jun 2014 07:37:14 PM EDT
# Purpose : A RHEL/CentOS - specific OS plugin for New Relic

import json
import psutil
import urllib2
import httplib
import ConfigParser
import os
import sys
import time
import logging
import socket
import nfsiostat
import _version

class NFSPlugin(object):
    """ NFS iostat plugin for newrelic
    """

    def __init__(self, debug=False, conf='/etc/newrelic-nfsiostat.conf'):

        # Some static constants (should be somewhere else probably)
        self.guid = 'com.deliveryagent.newrelic.nfsiostat'
        self.name = 'NFS Statistics'
        self.api_url = 'https://platform-api.newrelic.com/platform/v1/metrics'
        self.version = _version.__version__
        self.config_file = conf
        self.duration = 0           # period of time since start or last successful push
        self.duration_start = int(time.time())
        socket.setdefaulttimeout(5)

        #store some system info
        self.uname = os.uname()
        self.pid = os.getpid()
        self.hostname = self.uname[1]  #this will likely be Linux-specific, but I don't want to load a whole module to get a hostname another way
        self.kernel = self.uname[2]
        self.arch = self.uname[4]

        self.debug = debug

        # Variables to hold various stats
        self.metric_data = {}
        self.json_data = {}     #a construct to hold the json call data as we build it
        self.nfs_stats = {}
        self.nfs_stats_old = {}
        self.nfs_stats_current = {}

        # This is hackery to format the "float" values reasonably
        json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')

        self.first_run = True   #this is set to False after the first run function is called
        self._build_agent_stanza()
        self._parse_config()

    def _parse_config(self):
        # Open the config and log files in their own try/except
        try:
            config = ConfigParser.RawConfigParser()
            dataset = config.read(self.config_file)
            if len(dataset) < 1:
                raise ValueError, "Failed to open/find config files"
          
            logfilename = config.get('plugin','logfile')
            loglevel = config.get('plugin','loglevel')
            logging.basicConfig(filename=logfilename,
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s: %(message)s',
                    )
            self.logger = logging.getLogger(__name__)
            if self.debug:
                # DEBUG logs!
                console = logging.StreamHandler()
                formatter = logging.Formatter('%(levelname)-8s %(name)s:%(funcName)s: %(message)s')
                console.setLevel(logging.DEBUG)
                console.setFormatter(formatter)
                self.logger.addHandler(console)
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(loglevel)

        except Exception, e:
            # Might be nice to properly catch this and emit a nice message?
            # Can't depend on "logger" here
            raise e

        try:
            self.license_key = config.get('plugin', 'key')
            self.pid_file = config.get('plugin', 'pidfile')
            self.interval = config.getint('plugin', 'interval')
            self.enable_nfs_aggregate = config.getboolean('plugin','enable_nfs_aggregate')
            self.enable_nfs_reportvolumes = config.getboolean('plugin','enable_nfs_reportvolumes')
            self.enable_proxy = config.getboolean('proxy','enable_proxy')

            if self.enable_proxy:
                proxy_host = config.get('proxy','proxy_host')
                proxy_port = config.get('proxy','proxy_port')
                # These proxy_setttings will be used by urllib2
                self.proxy_settings = {
                        'http': '%s:%s' % (proxy_host, proxy_port),
                        'https': '%s:%s' % (proxy_host, proxy_port)
                }
                self.logger.info("Configured to use proxy: %s:%s" % (proxy_host, proxy_port))
            # Initialize NFS related values
            self.nfs_device_list = json.loads(config.get('nfs','device_list'))
            self.nfs_ops = ['Read','Write','GetAttr','Access','Lookup','ReadDir','ReadDirPlus']

        except Exception, e:
            self.logger.exception(e)
            raise e

    def _update_nfs_stats(self):
        '''mostly borrowed from nfsiostat(.py), to update the NFS stat data'''
        current_stats = {}
        diff_stats = {}
        old_stats = self.nfs_stats_old
        mountstats = nfsiostat.parse_stats_file('/proc/self/mountstats')
        devices = nfsiostat.list_nfs_mounts(self.nfs_device_list,mountstats)

        if old_stats:
            # Trim device list to only include intersection of old_stats and mountstats data,
            # this addresses umounts due to autofs mountpoints
            devicelist = filter(lambda x:x in devices,old_stats)
        else:
            devicelist = devices
    
        for device in devicelist:
            current_stats[device] = nfsiostat.DeviceData()
            current_stats[device].parse_stats(mountstats[device])
            if old_stats:
                diff_stats[device] = current_stats[device].compare_iostats(old_stats[device])
            if self.enable_nfs_aggregate:
                if 'ALL' in current_stats:
                    current_stats['ALL'] = current_stats['ALL'].combine_iostats(current_stats[device])
                else:
                    current_stats['ALL'] = nfsiostat.DeviceData()
                    current_stats['ALL'].parse_stats(mountstats[device])

        # Get diffs of aggregate stats
        if self.enable_nfs_aggregate and old_stats:
            diff_stats['ALL'] = current_stats['ALL'].compare_iostats(old_stats['ALL'])
        
        # Get ready for next iteration
        # NOTE: If the newrelic push is successful, we will update
        #  self.nfs_stats_old with the current nfs_stats
        self.nfs_stats_current = current_stats
        self.nfs_stats = diff_stats
        # Return list of mounts
        return devicelist

    def _get_nfs_stat_for(self, volume, prefix='Component/NFS/Volume'):
        '''this will add NFS stats for a given NFS mount to metric_data'''
        # This is mostly borrowed from nfsiostat display_iostats and its __print partners
        self.logger.debug("processing NFS volume - %s" % volume)
        try:
            prefix += volume + '/'
            volnfsstat = self.nfs_stats[volume]
            nfs_data = {
                prefix + 'Total/Operations[ops/second]': volnfsstat.ops(self.duration),
                prefix + 'RPC Backlog[calls]': volnfsstat.backlog(self.duration),
            }

            for op in (self.nfs_ops):
                if op.upper() == 'READDIRPLUS' and not volnfsstat.has_readdirplus():
                    # NFSv4 mounts do not have READDIRPLUS
                    continue
                op_stat = volnfsstat.get_rpc_op_stats(op.upper(), self.duration)
                op_prefix = prefix + op
                op_data = {
                    op_prefix + '/Operations[ops/second]': op_stat[0],
                    op_prefix + '/Volume[KibiBytes/second]': op_stat[1],
                    op_prefix + '/Retransmits[calls]': op_stat[3],
                    op_prefix + '/RetransmitPercent[calls]': op_stat[3],
                    op_prefix + '/Average/Size[KibiBytes/Operation]': op_stat[2],
                    op_prefix + '/Average/RTT[ms/operation]': op_stat[5],
                    op_prefix + '/Average/Execute Time[ms/operation]': op_stat[6],
                }
                nfs_data.update(op_data)
            # There is more NFS data that could be collected here

            for k,v in nfs_data.items():
                self.metric_data[k] = v
        except Exception, e:
            self.logger.exception(e)
            pass

    def _get_nfs_stats(self):
        '''this is called to iterate through all NFS mounts on a system and collate the data'''
        try:
            mounts = self._update_nfs_stats()
            if self.enable_nfs_reportvolumes:
                for vol in mounts:
                    self._get_nfs_stat_for(vol)
            if self.enable_nfs_aggregate:
                self._get_nfs_stat_for('ALL','Component/NFS/')
        except Exception, e:
            self.logger.exception(e)
            pass

    def _build_agent_stanza(self):
        '''this will build the 'agent' stanza of the new relic json call'''
        try:
            values = {}
            values['host'] = self.hostname
            values['pid'] = self.pid
            values['version'] = self.version

            self.json_data['agent'] = values
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _reset_json_data(self):
        '''this will 'reset' the json data structure and prepare for the next call. It does this by mimicing what happens in __init__'''
        try:
            self.metric_data = {}
            self.json_data = {}
            self._build_agent_stanza()
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _build_component_stanza(self):
        '''this will build the 'component' stanza for the new relic json call'''
        try:
            # Set duration for use in other calculations
            self.duration =  int(time.time()) - self.duration_start
            c_list = []
            c_dict = {}
            c_dict['name'] = self.hostname
            c_dict['guid'] = self.guid
            c_dict['duration'] = self.duration

            self._get_nfs_stats()

            c_dict['metrics'] = self.metric_data
            c_list.append(c_dict)

            self.json_data['components'] = c_list
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _prep_first_run(self):
        '''this will prime the needed buffers to present valid data when math is needed'''
        try:
            #create the first counter values to do math against for network, disk and swap
            self._update_nfs_stats()

            # Pretend run was successful to get stats initialized properly
            self._successful_run_reset()

            #sleep so the math represents  (interval) second intervals when we actually run
            self.logger.debug("First Run! Sleeping %d seconds..." % self.interval)
            time.sleep(self.interval)
            self.first_run = False
            return True
        except Exception, e:
            self.logger.exception(e)
            raise e

    def _successful_run_reset(self):
        ''' This will reset the statistics upon successful run'''
        self.duration_start = int(time.time())
        self.nfs_stats_old = self.nfs_stats_current

    def add_to_newrelic(self):
        '''this will glue it all together into a json request and execute'''
        if self.first_run:
            self._prep_first_run()  #prime the data buffers if it's the first loop

        self._build_component_stanza()  #get the data added up
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(json.dumps(self.json_data))
        try:
            if self.enable_proxy:
                proxy_handler = urllib2.ProxyHandler(self.proxy_settings)
                opener = urllib2.build_opener(proxy_handler)
            else:
                opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())

            request = urllib2.Request(self.api_url)
            request.add_header("X-License-Key", self.license_key)
            request.add_header("Content-Type","application/json")
            request.add_header("Accept","application/json")

            response = opener.open(request, json.dumps(self.json_data))

            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Duration: %s (sec)" % self.duration)
                self.logger.debug("%s (%s)" % (request.get_full_url(), response.getcode()))
                self.logger.debug('Response: %s' % response.read())

            if response.code == 200:
                # Only reset on success (allows the exceptions below to continue)
                self._successful_run_reset()

            response.close()

        except httplib.HTTPException, e:
            self.logger.error('HTTP Exception: %s' % e)
            pass    # continue on this error

        except urllib2.HTTPError, e:
            self.logger.error('HTTP Error: %s' % e)
            self.logger.debug('HTTP Error Details: %s' % e.read())
            pass    # continue

        except urllib2.URLError, e:
            # URLError (DNS Error?)
            self.logger.error('URL Error: %s' % e.reason)
            pass    # continue
        self._reset_json_data()
