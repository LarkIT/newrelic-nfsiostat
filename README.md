NewRelic-NFSIOStat
=========

A New Relic Plugin that gathers data from nfsiostat to push to newrelic.

This is "tested" on CentOS 6, but should work on RHEL/CentOS/etc 5-7.

# Monitoring Highlights

* Detailed NFS Statistics for ALL mountpoints or a "list"

# Requirements
* Python 2.6.x or 2.7.x 
* Linux Kernel with /proc/self/mountstats
* NFS Mounted Filesystems to monitor ;)

# Installation

* Download the RPM from the latest https://github.com/DeliveryAgent/newrelic-nfsiostat/releases
* yum localinstall (filename).rpm

# Configuration
* EDIT: /etc/newrelic-nfsiostat.conf
  * Set your license key in the key setting
  * Enable proxy if necessary

# Start/Stop Service
* service newrelic-nfsiostat start

* service newrelic-nfsiostat stop


# Source Installation (experts only)
* Build RPM
    * Dowload the source and execute:  

    ```
    python setup.py sdist_rpm
    cd dist/
    yum localinstall <RPM You Just Made>.rpm
    ```  
    
* Source Distribution
    * Download the source and execute:  

    ```
    python setup.py sdist
    cd dist/
    tar zxf <The Tarball>
    cd <The Directory you just unzipped>
    python setup.py install
    ```
