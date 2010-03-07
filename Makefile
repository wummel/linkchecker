# This Makefile is only used by developers.
PYVER:=2.6
PYTHON:=python$(PYVER)
VERSION:=$(shell $(PYTHON) setup.py --version)
MACHINE:=$(shell uname -m)
HOST:=www.debian.org
LCOPTS:=-Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -Fgxml -Fdot -v -r1 -C
PYTHONSRC:=/home/calvin/src/python-gitsvn
PY_FILES_DIRS:=linkcheck tests *.py linkchecker cgi-bin config doc
TESTS ?= tests/
# set test options, eg. to "--nologcapture"
TESTOPTS=
PAGER ?= less
# build dir for debian package
BUILDDIR:=$(HOME)/packages/official
DEB_ORIG_TARGET:=$(BUILDDIR)/linkchecker_$(VERSION).orig.tar.gz
# original dnspython repository module
DNSPYTHON:=$(HOME)/src/dnspython-git/dns
# options to run the pep8 utility
PEP8OPTS:=--repeat --ignore=E211,E501 --exclude=dns


.PHONY: all
all:
	@echo "Read the file INSTALL.txt to see how to build and install this package."

.PHONY: clean
clean:
	-$(PYTHON) setup.py clean --all
	rm -f linkchecker-out.* *-stamp*
	$(MAKE) -C po clean
	$(MAKE) -C doc/html clean
	$(MAKE) -C linkcheck/HtmlParser clean
	rm -f linkcheck/network/_network.so
	find . -name '*.py[co]' -exec rm -f {} \;

.PHONY: distclean
distclean: clean cleandeb
	rm -rf build linkchecker.egg-info
	rm -f _LinkChecker_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f linkchecker-out* linkchecker.prof
	rm -rf LinkChecker-$(VERSION)
	rm -rf coverage dist-stamp python-build-stamp*

.PHONY: cleandeb
cleandeb:
	rm -rf debian/linkchecker debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

MANIFEST: MANIFEST.in setup.py
	$(PYTHON) setup.py sdist --manifest-only

.PHONY: locale
locale:
	$(MAKE) -C po

# to build in the current directory
.PHONY: localbuild
localbuild: MANIFEST
	$(MAKE) -C doc/html
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py build
	cp -f build/lib.linux-$(MACHINE)-$(PYVER)/linkcheck/HtmlParser/htmlsax.so linkcheck/HtmlParser
	cp -f build/lib.linux-$(MACHINE)-$(PYVER)/linkcheck/network/_network.so linkcheck/network

.PHONY: deb_orig
deb_orig:
	if [ ! -e $(DEB_ORIG_TARGET) ]; then \
	  $(MAKE) dist-stamp && \
	  cp dist/LinkChecker-$(VERSION).tar.gz $(DEB_ORIG_TARGET); \
	fi

.PHONY: upload
upload:
	rsync -avP -e ssh dist/* calvin,linkchecker@frs.sourceforge.net:/home/frs/project/l/li/linkchecker/$(VERSION)/


.PHONY: release
release: distclean releasecheck dist-stamp sign_distfiles upload
	@echo "Updating LinkChecker Homepage..."
	$(MAKE) -C ~/public_html/linkchecker.sf.net update upload
	@echo "Register at Python Package Index..."
	$(PYTHON) setup.py register

.PHONY: chmod
chmod:
	-chmod -R a+rX,u+w,go-w -- *
	find . -type d -exec chmod 755 {} \;

.PHONY: dist
dist: locale MANIFEST chmod
	$(PYTHON) setup.py sdist --formats=gztar
# no rpm buildable with bdist_rpm, presumable due to this bug:
# https://bugzilla.redhat.com/show_bug.cgi?id=236535
# too uninvolved to fix it

dist-stamp: changelog
	$(MAKE) dist
	touch $@

# The check programs used here are mostly local scripts on my private system.
# So for other developers there is no need to execute this target.
.PHONY: check
check:
	[ ! -d .svn ] || check-nosvneolstyle -v
	check-copyright
	check-pofiles -v
	py-tabdaddy
	py-unittest2-compat tests/
	$(MAKE) pyflakes

filescheck:
	-./linkchecker $(LCOPTS) http://$(HOST)/

update-copyright:
	update-copyright --holder="Bastian Kleineidam"

.PHONY: releasecheck
releasecheck: check
	@if egrep -i "xx\.|xxxx|\.xx" doc/changelog.txt > /dev/null; then \
	  echo "Could not release: edit doc/changelog.txt release date"; false; \
	fi
#	$(MAKE) -C doc test

.PHONY: sign_distfiles
sign_distfiles:
	for f in dist/*; do \
	  if [ ! -f $${f}.asc ]; then \
	    gpg --detach-sign --armor $$f; \
	  fi; \
	done

.PHONY: test
test:	localbuild
	$(PYTHON) /usr/bin/nosetests -v -m "^test_.*" $(TESTOPTS) $(TESTS)

.PHONY: pyflakes
pyflakes:
	pyflakes $(PY_FILES_DIRS) 2>&1 | \
          grep -v "redefinition of unused 'linkcheck'" | \
          grep -v "undefined name '_'" | \
	  grep -v "undefined name '_n'" | cat

.PHONY: pep8
pep8:
	pep8 $(PEP8OPTS) $(PY_FILES_DIRS)

.PHONY: reindent
reindent:
	$(PYTHON) config/reindent.py -r -v linkcheck

# Compare custom Python files with the original ones from subversion.
.PHONY: diff
diff:
	@for f in gzip robotparser httplib; do \
	  echo "Comparing $${f}.py"; \
	  diff -u linkcheck/$${f}2.py $(PYTHONSRC)/Lib/$${f}.py | $(PAGER); \
	done

.PHONY: dnsdiff
dnsdiff:
	diff -BurN --exclude=changelog.txt linkcheck/dns $(DNSPYTHON) | $(PAGER)

.PHONY: changelog
changelog:
	sftrack_changelog linkchecker calvin@users.sourceforge.net doc/changelog.txt

.PHONY: gui
gui:
	$(MAKE) -C linkcheck/gui
