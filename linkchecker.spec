%define name linkchecker
%define version 1.12.3
%define release 1

Summary: check HTML documents for broken links
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Web/Utilities
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
Vendor: Bastian Kleineidam <calvin@users.sourceforge.net>
Packager: Bastian Kleineidam <calvin@users.sourceforge.net>
Provides: linkchecker
Url: http://linkchecker.sourceforge.net/

%description
Linkchecker features
o recursive checking
o multithreading
o output in colored or normal text, HTML, SQL, CSV or a sitemap
  graph in GML or XML.
o HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Gopher, Telnet and local
  file links support
o restriction of link checking with regular expression filters for URLs
o proxy support
o username/password authorization for HTTP and FTP
o robots.txt exclusion protocol support
o Cookie support
o i18n support
o a command line interface
o a (Fast)CGI web interface (requires HTTP server)


%prep
%setup

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
# fix it so that it works even if things become a bz2 automatically
perl -pi -e 's/(linkchecker\.1)\.gz/$1.*/' INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc INSTALL README TODO lconline/ test/
