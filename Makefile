# This Makefile is only used by developers.
PYTHON := python2.3
VERSION = $(shell $(PYTHON) setup.py --version)
PACKAGE := linkchecker
NAME = $(shell $(PYTHON) setup.py --name)
PACKAGEDIR = /home/groups/l/li/$(PACKAGE)
#HTMLDIR=shell1.sourceforge.net:$(PACKAGEDIR)/htdocs
HTMLDIR=/home/calvin/public_html/linkchecker.sf.net/htdocs
#HOST=treasure.calvinsplayground.de
HOST=www.debian.org
#LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s -r1
DESTDIR = /.
MD5SUMS := linkchecker-md5sums.txt
PYCHECKEROPTS := -F config/pycheckrc
PYLINTOPTS := 
# --ignore=httplib2.py
PYFILES := linkcheck/*.py linkcheck/logger/*.py linkcheck/checker/*.py
TESTFILES := linkcheck/tests/*.py linkcheck/ftests/*.py

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
# ignore errors of this command
	-$(PYTHON) setup.py clean --all
	$(MAKE) -C po clean
	rm -f linkcheck/HtmlParser/htmlsax.so
	rm -f linkcheck/HtmlParser/*.output
	find . -name '*.py[co]' | xargs rm -f

distclean: clean cleandeb
# just to be sure clean also the build dir
	rm -rf dist build
	rm -f VERSION _$(PACKAGE)_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f $(PACKAGE)-out* $(PACKAGE).prof $(PACKAGE)-md5sums.txt

cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

config:
	$(PYTHON) setup.py config -lcrypto

dist:	releasecheck distclean locale config
	$(PYTHON) setup.py sdist --formats=gztar bdist_rpm

# to build in the current directory (assumes python 2.3)
localbuild:
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py build
	cp -f build/lib.linux-i686-2.3/linkcheck/HtmlParser/htmlsax.so linkcheck/HtmlParser

# produce the .deb Debian package
deb_local: cleandeb
# standard for local use
	fakeroot debian/rules binary

deb_signed: cleandeb
# ready for upload, signed with my GPG key
	env CVSROOT=:ext:calvin@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -sgpg -pgpg -k32EC6F3E -r"fakeroot --" -I.cvsignore

files:	locale localbuild
	env http_proxy="" LANG=C $(PYTHON) $(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/
	rm -f linkchecker-out.*.gz
	for f in linkchecker-out.*; do gzip --best $$f; done

VERSION:
	echo $(VERSION) > VERSION

upload:
	rm -f $(MD5SUMS)
	md5sum dist/* > $(MD5SUMS)
	for f in dist/*; do gpg --detach-sign --armor $$f; done
	ncftpput upload.sourceforge.net /incoming dist/*

homepage: files VERSION
	cp ChangeLog $(HTMLDIR)/changes.txt
	cp README $(HTMLDIR)/readme.txt
	cp linkchecker-out.*.gz $(HTMLDIR)
	cp VERSION $(HTMLDIR)/raw/
	cp $(MD5SUMS) $(HTMLDIR)/

test:
	test/run.sh test.py --resource=network --search-in=linkcheck -fupv

coverage:
	test/run.sh test.py --coverage

locale:
	$(MAKE) -C po

timeouttest:
	$(PYTHON) $(PACKAGE) -v --timeout=0 mailto:root@aol.com

tar:	distclean
	cd .. && tar cjvf linkchecker.tar.bz2 linkchecker

releasecheck:
	@if grep xxxx ChangeLog > /dev/null; then \
	  echo "Could not release: edit ChangeLog release date"; false; \
	fi

pycheck:
	-env PYTHONPATH=. PYTHONVER=2.3 pychecker $(PYCHECKEROPTS) $(PYFILES)

pylint:
	-env PYTHONPATH=. PYLINTRC=config/pylintrc pylint $(PYLINTOPTS) $(PYFILES) $(TESTFILES)

reindent:
	$(PYTHON) config/reindent.py -r -v linkcheck

.PHONY: all clean cleandeb distclean files upload test timeouttest locale
.PHONY: onlinetest config dist deb_local deb_signed deb_unsigned tar
.PHONY: releasecheck pycheck pylint reindent
