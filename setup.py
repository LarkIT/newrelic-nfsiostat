#!/usr/bin/env python

from distutils.core import setup, Extension
import ConfigParser
import os

releaseFile = open('/etc/redhat-release','r')
distro_test = releaseFile.read()
d_version = distro_test[0].split()[0]
if d_version == 'Fedora':
    on_fedora = True
else:
    on_fedora = False

exec(open('src/_version.py').read())
name = 'newrelic-nfsiostat'
version = __version__
data_files=[
    ('/etc',['conf/newrelic-nfsiostat.conf']),
    ('/usr/share/doc/%s-%s'% (name, version), ['doc/README','doc/LICENSE']),
]
if on_fedora:
    data_files.append(('/usr/lib/systemd/system', ['scripts/newrelic-nfsiostat.service']))
else:
    data_files.append(('/etc/rc.d/init.d', ['scripts/init/newrelic-nfsiostat']))
 
setup(
    name=name,
    version=version,
    description='NFSIOSTAT monitoring plugin for New Relic',
    author='Tommy McNeely',
    author_email='tommy@lark-it.com',
    url='https://github.com/DeliveryAgent/newrelic-nfsiostat',
    maintainer='Tommy McNeely',
    maintainer_email = 'tommy@lark-it.com',
    long_description='A plugin for New Relic (http://www.newrelic.com) to gather nfsiostat data',
    packages=['newrelic-nfsiostat'],
    package_dir={'newrelic-nfsiostat': 'src'},
    scripts = ['scripts/newrelic-nfsiostat'],
    data_files = data_files,
   )


