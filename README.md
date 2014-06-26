NewRelic-NFSIOStat
=========

A New Relic Plugin that gathers data from nfsiostat to push to newrelic.

This is "tested" on CentOS 6, but should work on RHEL/CentOS/etc 5-7.

Monitoring Highlights
---------------------

* Detailed NFS Statistics for ALL mountpoints or a "list"


Installation
------------
* RPM
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
