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

* Download the RPM from the latest [release](https://github.com/DeliveryAgent/newrelic-nfsiostat/releases)
* yum localinstall (filename).rpm

# Configuration
* EDIT: /etc/newrelic-nfsiostat.conf
  * Set your license key in the key setting
  * Enable proxy if necessary

# Start/Stop Service
* service newrelic-nfsiostat start

* service newrelic-nfsiostat stop


# Source
This type of installation is for experts only
* https://github.com/DeliveryAgent/newrelic-nfsiostat
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

# License
We are loosely using GPLv2, withiout having really read or understood the consequences or benefits.

# Support
Support is only on a best effort basis. We are using this module, it works for us. Your milege may vary. Please file an issue in GitHub if you have problems, suggestions, etc.

Please Fork, branch and submit pull requests :)
