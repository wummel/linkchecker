# This Makefile is only used by developers.
# You will need a Debian Linux system to use this Makefile!
VERSION=$(shell python setup.py --version)
PACKAGE = linkchecker
NAME = $(shell python setup.py --name)
HOST=fsinfo.cs.uni-sb.de
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -R -t0 -v
DEBPACKAGE = $(PACKAGE)_$(VERSION)_i386.deb
SOURCES = \
linkcheck/Config.py \
linkcheck/FileUrlData.py \
linkcheck/FtpUrlData.py \
linkcheck/GopherUrlData.py \
linkcheck/HostCheckingUrlData.py \
linkcheck/HttpUrlData.py \
linkcheck/HttpsUrlData.py \
linkcheck/JavascriptUrlData.py \
linkcheck/Logging.py \
linkcheck/MailtoUrlData.py \
linkcheck/NntpUrlData.py \
linkcheck/TelnetUrlData.py \
linkcheck/Threader.py \
linkcheck/UrlData.py \
linkcheck/__init__.py \
linkcheck/lc_cgi.py \
linkchecker

DESTDIR=/.
.PHONY: test clean distclean package files upload dist locale all

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
	-python setup.py clean --all
	$(MAKE) -C po clean

distclean: clean cleandeb
	rm -rf dist
	rm -f $(PACKAGE)-out.* VERSION LinkCheckerConf.py* MANIFEST

cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

dist:	locale
	fakeroot debian/rules binary
	# cleandeb because distutils choke on dangling symlinks
	# (linkchecker.1 -> undocumented.1)
	$(MAKE) cleandeb
	python setup.py sdist --formats=gztar,zip bdist_rpm
	# extra run without SSL compilation
	python setup.py bdist_wininst
	mv -f ../$(DEBPACKAGE) dist

package:
	cd dist && dpkg-scanpackages . ../override.txt | gzip --best > Packages.gz

files:	locale
	./$(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/~calvin/

VERSION:
	echo $(VERSION) > VERSION

upload: distclean dist package files VERSION
	scp debian/changelog shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/changes.txt
	scp linkchecker-out.* shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs
	scp VERSION shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/raw/
	scp dist/* shell1.sourceforge.net:/home/groups/ftp/pub/$(PACKAGE)/
	ssh -C -t shell1.sourceforge.net "cd /home/groups/$(PACKAGE) && make"

test:
	rm -f test/*.result
	@for i in test/*.html; do \
	  echo "Testing $$i. Results are in $$i.result"; \
	  ./$(PACKAGE) -r1 -o text -N"news.rz.uni-sb.de" -v -a $$i > $$i.result 2>&1; \
        done

locale:
	$(MAKE) -C po
