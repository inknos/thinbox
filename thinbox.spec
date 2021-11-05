%define debug_package %{nil}

Name:           thinbox
Version:        0.1.0
Release:        1%{?dist}
Summary:        Thinbox is a tool to create and manage virtual machines

License:        GPLv3
URL:            https://github.com/inknos/thinbox
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

Requires:       python3-argcomplete
Requires:       python3-beautifulsoup4.noarch
Requires:       python3-paramiko
Requires:       python3-requests
Requires:       python3-scp
Requires:       util-linux
Requires:       libvirt-client

%description


%prep
%autosetup


%build


%install
rm -rf $RPM_BUILD_ROOT
install -Dpm 0755 %{name}.py %{buildroot}%{_bindir}/%{name}


%files
%{_bindir}/%{name}
%license LICENSE


%changelog
* Fri Nov 05 2021 Nicola Sella <nsella@redhat.com> - 0.1.0-1
- Updated command line pull options
- Many bugfixes

* Fri Nov 05 2021 Nicola Sella <nsella@redhat.com> - 0.0.0-1
- Initial Release
