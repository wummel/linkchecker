# This Makefile is only used by developers.
PYTHON=python2.2
VERSION=$(shell $(PYTHON) setup.py --version)
PACKAGE=linkchecker
NAME=$(shell $(PYTHON) setup.py --name)
PACKAGEDIR=/home/groups/l/li/$(PACKAGE)
#HTMLDIR=shell1.sourceforge.net:$(PACKAGEDIR)/htdocs
HTMLDIR=/home/calvin/public_html/linkchecker.sf.net/htdocs
#HOST=treasure.calvinsplayground.de
HOST=www.debianplanet.org
#LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s -r1
TEST=env LANG=C ftp_proxy="" http_proxy="" $(PYTHON) test/regrtest.py
OFFLINETESTS = test_base test_misc test_file test_frames
ONLINETESTS = test_mail test_http test_https test_news test_ftp test_telnet
DESTDIR=/.
MD5SUMS=linkchecker-md5sums.txt

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
	-$(PYTHON) setup.py clean --all # ignore errors of this command
	$(MAKE) -C po clean
	rm -f linkcheck/parser/htmlsax.so
	find . -name '*.py[co]' | xargs rm -f

distclean: clean cleandeb
	rm -rf dist build # just to be sure clean also the build dir
	rm -f VERSION VERSION-DEVEL _$(PACKAGE)_configdata.py MANIFEST Packages.gz
	# clean aborted dist builds and -out files
	rm -f $(PACKAGE)-*

cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

config:
	$(PYTHON) setup.py config -lcrypto

# no rpm package; too much trouble, cannot test
dist:	locale config
	$(PYTHON) setup.py sdist --formats=gztar bdist_rpm
	rm -f $(MD5SUMS)
	md5sum dist/* > $(MD5SUMS)
	for f in dist/*; do gpg --detach-sign --armor $$f; done

# to build in the current directory (assumes python 2.2)
localbuild:
	$(MAKE) -C linkcheck/parser
	$(PYTHON) setup.py build
	cp -f build/lib.linux-i686-2.2/linkcheck/parser/htmlsax.so linkcheck/parser


# produce the .deb Debian package
deb_local: cleandeb
	# standard for local use
	fakeroot debian/rules binary

deb_localsigned:
	debuild -sgpg -pgpg -k32EC6F3E -r"fakeroot --"

deb_signed: cleandeb
	# ready for upload, signed with my GPG key
	env CVSROOT=:pserver:anonymous@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -sgpg -pgpg -k32EC6F3E -r"fakeroot --"

deb_unsigned: cleandeb
	# same thing, but unsigned (for local archives)
	env CVSROOT=:pserver:anonymous@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -us -uc -r"fakeroot --"

files:	locale localbuild
	env http_proxy="" LANG=C $(PYTHON) $(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/
	rm -f linkchecker-out.*.gz
	for f in linkchecker-out.*; do gzip --best $$f; done

VERSION:
	echo $(VERSION) > VERSION

VERSION-DEVEL:
	echo $(VERSION) > VERSION-DEVEL

upload: distclean dist files VERSION homepage
	ncftpput upload.sourceforge.net /incoming dist/*

homepage:
	cp ChangeLog $(HTMLDIR)/changes.txt
	cp README $(HTMLDIR)/readme.txt
	cp linkchecker-out.*.gz $(HTMLDIR)
	cp VERSION $(HTMLDIR)/raw/
	cp $(MD5SUMS) $(HTMLDIR)/

upload-devel: distclean dist VERSION-DEVEL
	scp ChangeLog $(HTMLDIR)/changes-devel.txt
	scp VERSION-DEVEL $(HTMLDIR)/raw/
	#scp dist/* $(HTMLDIR)/
	ncftpput upload.sourceforge.net /incoming dist/* && read -p "Make new SF file releases and then press Enter:"
	ssh -C -t shell1.sourceforge.net "cd $(PACKAGEDIR) && make"

test:
	$(TEST) $(OFFLINETESTS)

onlinetest:
	$(TEST) $(ONLINETESTS)

locale:
	$(MAKE) -C po

timeouttest:
	$(PYTHON) $(PACKAGE) -v --timeout=0 mailto:root@aol.com

tar:	distclean
	cd .. && tar cjvf linkchecker.tar.bz2 linkchecker

.PHONY: all clean cleandeb distclean files upload test timeouttest locale
.PHONY: onlinetest config dist deb_local deb_signed deb_unsigned tar
.PHONY: upload-devel
