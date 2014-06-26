### SPEC for newrelic-nfsiostat

# EL5 will require python26 from EPEL
%if 0%{rhel} == 5
%global pyver 26
%global pybasever 2.6
%global __os_install_post %{__python26_os_install_post}
%else
%global pyver 2
%global pybasever 2
%endif

# Not sure about others

%global __python2 %{_bindir}/python%{pybasever}

%{!?python2_sitelib: %define python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?_initddir: %define _initddir /etc/rc.d/init.d }


Summary: NFSIOSTAT plugin for New Relic
Name: newrelic-nfsiostat
Version: 0.1.0
Release: 1%{?dist}
Source0: https://github.com/DeliveryAgent/newrelic-nfsiostat/archive/%{name}-%{version}.tar.gz
License: GPLv2
Group: Applications/System
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXXX)
BuildRequires: python%{pyver}-devel
BuildRequires: python-setuptools
BuildArch: noarch
Requires: python%{pyver}
Requires: python-daemon

# RHEL 5 has to use python26-psutils
%if 0%{rhel} == 5
Requires: python%{pyver}-psutil
%else
Requires: python-psutil
%endif

# RHEL7 and Fedora have different requirements
%if ! (0%{?rhel} >= 7 || 0%{?fedora} >= 15)
Requires: chkconfig
Requires: initscripts
%else
%if 0%{?systemd_preun:1}
Requires(post): systemd-units
%endif
BuildRequires: systemd-units
%endif

Vendor: Tommy McNeely <tommy@lark-it.com>
Url: https://github.com/DeliveryAgent/newrelic-nfsiostat

%description
A New Relic plugin to send statistics from nfsiostat to NewRelic

%prep
%setup -q -n %{name}-%{version}

%build
%{__python2} setup.py build

%install
%{__rm} -rf %{buildroot}
%{__python2} setup.py install -O1 --root=$RPM_BUILD_ROOT

%clean
rm -rf %{buildroot}

%post
%if (0%{?rhel} >= 7 || 0%{?fedora} >= 15)
/bin/systemctl enable newrelic-nfsiostat.service
%else
/sbin/chkconfig --add newrelic-nfsiostat
%endif

%files
%defattr(-,root,root,-)
%config(noreplace) /etc/newrelic-nfsiostat.conf
%if (0%{?rhel} >= 7 || 0%{?fedora} >= 15)
%{_unitdir}/newrelic-nfsiostat.service
%else
%config %attr(0755, root, root) %{_initddir}/newrelic-nfsiostat
%endif

%dir %{_docdir}/%{name}-%{version}
%{_docdir}/%{name}-%{version}/*
%{python2_sitelib}/*egg-info
%{python2_sitelib}/newrelic-nfsiostat/*
%{_bindir}/newrelic-nfsiostat

%changelog
* Thu Jun 26 2014 Tommy McNeely <tommy@lark-it.com> 0.1.0-1
- Initial RPM after forking from NewRHELic
