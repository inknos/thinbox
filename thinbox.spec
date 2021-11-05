%define debug_package %{nil}

Name:           thinbox
Version:        0.0.0
Release:        1%{?dist}
Summary:        Thinbox is a tool to create and manage virtual machines

License:        GPLv3
URL:            https://github.com/inknos/thinbox
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz

Requires:       python3-argcomplete
Requires:       python3-paramiko
Requires:       python3-scp

%description


%prep
%autosetup


%build


%install
rm -rf $RPM_BUILD_ROOT
install -Dpm 0755 %{name}.py %{buildroot}%{_bindir}/%{name}
pdoc --html thinbox


%files
%{_bindir}/%{name}
%license LICENSE
%doc html/thinbox.html


%changelog
* Fri Nov 05 2021 Nicola Sella <nsella@redhat.com> - 0.0.0-1
- Initial Release
