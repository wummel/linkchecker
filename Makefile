# This Makefile is only used by developers.
PYTHON=python2.1
VERSION=$(shell $(PYTHON) setup.py --version)
PACKAGE=linkchecker
NAME=$(shell $(PYTHON) setup.py --name)
PACKAGEDIR=/home/groups/l/li/$(PACKAGE)
HTMLDIR=shell1.sourceforge.net:$(PACKAGEDIR)/htdocs
#HOST=treasure.calvinsplayground.de
HOST=www.debian.org
#LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
OFFLINETESTS = test_base test_misc test_file test_frames
ONLINETESTS = test_mail test_http test_https test_news test_ftp
DESTDIR=/.

.PHONY: all
all:
	@echo "Read the file INSTALL to see how to build and install"

.PHONY: clean
clean:
	-$(PYTHON) setup.py clean --all # ignore errors of this command
	$(MAKE) -C po clean
	find . -name '*.py[co]' | xargs rm -f

.PHONY: distclean
distclean: clean cleandeb
	rm -rf dist build # just to be sure clean also the build dir
	rm -f VERSION _$(PACKAGE)_configdata.py MANIFEST Packages.gz
	# clean aborted dist builds and -out files
	rm -f $(PACKAGE)-*

.PHONY: cleandeb
cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

.PHONY: config
config:
	$(PYTHON) setup.py config -lcrypto

# no rpm package; too much trouble, cannot test
.PHONY: dist
dist:	locale config
	$(PYTHON) setup.py sdist --formats=gztar,zip bdist_wininst

deb:
	# cleandeb because distutils choke on dangling symlinks
	# (linkchecker.1 -> undocumented.1)
	$(MAKE) cleandeb
	fakeroot debian/rules binary
	#env CVSROOT=:pserver:anonymous@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -sgpg -pgpg -k959C340F -rfakeroot 
	env CVSROOT=:pserver:anonymous@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -us -uc -rfakeroot 

.PHONY: files
files:	locale
	env http_proxy="" $(PYTHON) $(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/

VERSION:
	echo $(VERSION) > VERSION

.PHONY: upload
upload: distclean dist files VERSION
	scp debian/changelog $(HTMLDIR)/changes.txt
	scp README $(HTMLDIR)/readme.txt
	scp linkchecker-out.* $(HTMLDIR)
	scp VERSION $(HTMLDIR)/raw/
	scp dist/* $(HTMLDIR)/
	ssh -C -t shell1.sourceforge.net "cd $(PACKAGEDIR) && make"

.PHONY: test
test:
	$(PYTHON) test/regrtest.py $(OFFLINETESTS)

.PHONY: onlinetest
onlinetest:
	$(PYTHON) test/regrtest.py $(ONLINETESTS)

.PHONY: locale
locale:
	$(MAKE) -C po

.PHONY: timeouttest
timeouttest:
	$(PYTHON) $(PACKAGE) -DDD --timeout=2 mailto:calvin@cs.uni-sb.de
