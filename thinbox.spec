%define debug_package %{nil}
%define name thinbox
%define version 0.4.0
%define release 1

Name:           %{name}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        Thinbox is a tool to create and manage virtual machines

License:        GPLv3
URL:            https://github.com/inknos/thinbox
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  python3
BuildRequires:  python3-setuptools
BuildRequires:  python3-sphinx

Requires:       guestfs-tools
Requires:       python3
Requires:       python3-argcomplete
Requires:       python3-beautifulsoup4
Requires:       python3-paramiko
Requires:       python3-requests
Requires:       python3-scp
Requires:       util-linux
Requires:       libvirt-client

%description


%prep
%autosetup

%build
python3 setup.py build
sphinx-build -b man -c source source/man/man1/ build/man

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -Dm0644 build/man/%{name}.1 %{buildroot}/%{_mandir}/man1/%{name}.1


%files -f INSTALLED_FILES
%{_bindir}/%{name}
%license LICENSE
%defattr(-,root,root)
%{_mandir}/man1/%{name}.1*


%changelog
* Wed Dec 01 2021 Nicola Sella <nsella@redhat.com> - 0.4.0-1
- Add man documentation in spec
- Fix minor bugs

* Mon Nov 15 2021 Nicola Sella <nsella@redhat.com> - 0.3.0-1
- Add documentation in Sphinx
- Add env command
- rewrite code

* Wed Nov 10 2021 Nicola Sella <nsella@redhat.com> - 0.2.0-1
- Rewrite using python3-libvirt
- Split files for better scalability

* Fri Nov 05 2021 Nicola Sella <nsella@redhat.com> - 0.1.0-1
- Fix broken dependency

* Fri Nov 05 2021 Nicola Sella <nsella@redhat.com> - 0.1.0-1
- Updated command line pull options
- Many bugfixes

* Fri Nov 05 2021 Nicola Sella <nsella@redhat.com> - 0.0.0-1
- Initial Release
