# This Makefile is only used by developers.
PYTHON := python2.3
PACKAGE := linkchecker
NAME = $(shell $(PYTHON) setup.py --name)
PACKAGEDIR = /home/groups/l/li/$(PACKAGE)
#HTMLDIR=shell1.sourceforge.net:$(PACKAGEDIR)/htdocs
HTMLDIR=/home/calvin/public_html/linkchecker.sf.net/htdocs
#HOST=treasure.calvinsplayground.de
HOST=www.debian.org
#LCOPTS=-Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -v -s
LCOPTS=-Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -v -s -r1
DESTDIR = /.
PYFILES := $(wildcard linkcheck/*.py linkcheck/logger/*.py \
	linkcheck/checker/*.py)
TESTFILES := $(wildcard linkcheck/tests/*.py linkcheck/ftests/*.py)
PYCHECKEROPTS := -F config/pycheckrc
PYLINT := env PYTHONPATH=. PYLINTRC=config/pylintrc pylint
PYLINTOPTS := 
PYLINTBROKEN = linkcheck/lc_cgi.py
PYLINTFILES = $(filter-out $(PYLINTBROKEN),$(PYFILES))

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
# ignore errors of this command
	-$(PYTHON) setup.py clean --all
	rm -f sign-stamp release-stamp
	$(MAKE) -C po clean
	rm -f linkcheck/HtmlParser/htmlsax.so
	rm -f linkcheck/HtmlParser/*.output
	find . -name '*.py[co]' | xargs rm -f

distclean: clean cleandeb
# just to be sure clean also the build dir
	rm -rf dist build
	rm -f _$(PACKAGE)_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f $(PACKAGE)-out* $(PACKAGE).prof $(PACKAGE)-md5sums.txt

cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

config:
	$(PYTHON) setup.py config -lcrypto

locale:
	$(MAKE) -C po

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

release: releasecheck dist upload homepage
	mozilla -remote "openUrl(https://sourceforge.net/projects/linkchecker, new-tab)"
	@echo "Make SF release and press return..."
	@read
	@echo "Uploading new LinkChecker Homepage..."
	$(MAKE) -C ~/public_html/linkchecker.sf.net upload

homepage:
	$(MAKE) -C doc homepage

dist: locale config
	$(PYTHON) setup.py sdist --formats=gztar bdist_rpm

releasecheck:
	@if grep -i xxxx ChangeLog > /dev/null; then \
	  echo "Could not release: edit ChangeLog release date"; false; \
	fi

upload:
	for f in dist/*; do \
	  if [ ! -f $${f}.asc ]; then \
	    gpg --detach-sign --armor $$f; \
	  fi; \
	done
	ncftpput upload.sourceforge.net /incoming dist/*

test:
	test/run.sh test.py --resource=network --search-in=linkcheck -fupv

coverage:
	test/run.sh test.py --coverage

tar:	distclean
	cd .. && tar cjvf linkchecker.tar.bz2 linkchecker

pycheck:
	-env PYTHONPATH=. PYTHONVER=2.3 pychecker $(PYCHECKEROPTS) $(PYFILES)

pylint:
	$(PYLINT) $(PYLINTOPTS) $(PYLINTFILES) $(TESTFILES)

reindent:
	$(PYTHON) config/reindent.py -r -v linkcheck

.PHONY: all clean cleandeb distclean files upload test timeouttest locale
.PHONY: config deb_local deb_signed tar releasecheck pycheck pylint reindent
