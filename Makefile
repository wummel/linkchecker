# This Makefile is only used by developers.
PYTHON=python2.1
VERSION=$(shell $(PYTHON) setup.py --version)
PACKAGE=linkchecker
NAME=$(shell $(PYTHON) setup.py --name)
PACKAGEDIR=/home/groups/l/li/$(PACKAGE)
HTMLDIR=shell1.sourceforge.net:$(PACKAGEDIR)/htdocs
#HOST=treasure.calvinsplayground.de
HOST=www.debianplanet.org
#LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s -r1
OFFLINETESTS = test_base test_misc test_file test_frames
ONLINETESTS = test_mail test_http test_https test_news test_ftp
DESTDIR=/.

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
	-$(PYTHON) setup.py clean --all # ignore errors of this command
	$(MAKE) -C po clean
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
	$(PYTHON) setup.py sdist --formats=gztar,zip bdist_wininst

# produce the .deb Debian package
deb_local: cleandeb
	# standard for local use
	fakeroot debian/rules binary

deb_localsigned:
	debuild -sgpg -pgpg -k32EC6F3E -rfakeroot

deb_signed: cleandeb
	# ready for upload, signed with my GPG key
	env CVSROOT=:pserver:anonymous@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -sgpg -pgpg -k32EC6F3E -rfakeroot 

deb_unsigned: cleandeb
	# same thing, but unsigned (for local archives)
	env CVSROOT=:pserver:anonymous@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -us -uc -rfakeroot 

files:	locale
	env http_proxy="" $(PYTHON) $(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/
	for f in linkchecker-out.*; do gzip --best $$f; done

VERSION:
	echo $(VERSION) > VERSION

VERSION-DEVEL:
	echo $(VERSION) > VERSION-DEVEL

upload: distclean dist files VERSION
	scp ChangeLog $(HTMLDIR)/changes.txt
	scp README $(HTMLDIR)/readme.txt
	scp linkchecker-out.*.gz $(HTMLDIR)
	scp VERSION $(HTMLDIR)/raw/
	#scp dist/* $(HTMLDIR)/
	ncftpput upload.sourceforge.net /incoming dist/* && read -p "Make new SF file releases and then press Enter:"
	ssh -C -t shell1.sourceforge.net "cd $(PACKAGEDIR) && make"

upload-devel: distclean dist VERSION-DEVEL
	scp ChangeLog $(HTMLDIR)/changes-devel.txt
	scp VERSION-DEVEL $(HTMLDIR)/raw/
	#scp dist/* $(HTMLDIR)/
	ncftpput upload.sourceforge.net /incoming dist/* && read -p "Make new SF file releases and then press Enter:"
	ssh -C -t shell1.sourceforge.net "cd $(PACKAGEDIR) && make"

test:
	env LANG=C $(PYTHON) test/regrtest.py $(OFFLINETESTS)

onlinetest:
	env LANG=C $(PYTHON) test/regrtest.py $(ONLINETESTS)

locale:
	$(MAKE) -C po

timeouttest:
	$(PYTHON) $(PACKAGE) -v --timeout=0 mailto:root@aol.com

tar:	distclean
	cd .. && tar cjvf linkchecker.tar.bz2 linkchecker

.PHONY: all clean cleandeb distclean files upload test timeouttest locale
.PHONY: onlinetest config dist deb_local deb_signed deb_unsigned tar
.PHONY: upload-devel
