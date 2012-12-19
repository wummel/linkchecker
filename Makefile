# This Makefile is only used by developers.
PYVER:=2.7
PYTHON?=python$(PYVER)
APPNAME:=$(shell $(PYTHON) setup.py --name)
LAPPNAME:=$(shell echo $(APPNAME)|tr "[A-Z]" "[a-z]")
VERSION:=$(shell $(PYTHON) setup.py --version)
PLATFORM:=$(shell $(PYTHON) -c "from distutils.util import get_platform; print get_platform()")
FILESCHECK_URL:=http://localhost/~calvin/
SRCDIR:=${HOME}/src
PY_FILES_DIRS:=linkcheck tests *.py linkchecker linkchecker-nagios linkchecker-gui cgi-bin config doc
TESTS ?= tests
# set test options, eg. to "--verbose"
TESTOPTS=
PAGER ?= less
# build dir for debian package
BUILDDIR:=$(HOME)/projects/debian/official
DEB_ORIG_TARGET:=$(BUILDDIR)/linkchecker_$(VERSION).orig.tar.xz
# original dnspython repository module
DNSPYTHON:=$(HOME)/src/dnspython-git
# options to run the pep8 utility
PEP8OPTS:=--repeat --ignore=E211,E501,E225,E301,E302,E241 \
   --exclude="gzip2.py,httplib2.py,robotparser2.py"
PY2APPOPTS ?=
ifeq ($(shell uname),Darwin)
  CHMODMINUSMINUS:=
  NUMPROCESSORS:=$(shell sysctl -n hw.ncpu)
else
  CHMODMINUSMINUS:=--
  NUMPROCESSORS:=$(shell grep -c processor /proc/cpuinfo)
endif
# Pytest options:
# - use multiple processors
# - write test results in file
PYTESTOPTS:=-n $(NUMPROCESSORS) --resultlog=testresults.txt --durations=0


all:
	@echo "Read the file doc/install.txt to see how to build and install this package."

clean:
	-$(PYTHON) setup.py clean --all
	rm -f $(LAPPNAME)-out.* *-stamp*
	$(MAKE) -C po clean
	$(MAKE) -C doc/html clean
	$(MAKE) -C linkcheck/HtmlParser clean
	rm -f linkcheck/network/_network*.so
	find . -name '*.py[co]' -exec rm -f {} \;

distclean: clean cleandeb
	rm -rf build dist $(APPNAME).egg-info
	rm -f _$(APPNAME)_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f $(LAPPNAME)-out* $(LAPPNAME).prof
	rm -f alexa*.log testresults.txt
	rm -rf $(APPNAME)-$(VERSION)
	rm -rf coverage dist-stamp python-build-stamp*

cleandeb:
	rm -rf debian/$(LAPPNAME) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

MANIFEST: MANIFEST.in setup.py
	$(PYTHON) setup.py sdist --manifest-only

locale:
	$(MAKE) -C po mofiles

# to build in the current directory
localbuild: MANIFEST locale
	$(MAKE) -C doc/html
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py build
	cp -f build/lib.$(PLATFORM)-$(PYVER)*/linkcheck/HtmlParser/htmlsax*.so linkcheck/HtmlParser
	cp -f build/lib.$(PLATFORM)-$(PYVER)*/linkcheck/network/_network*.so linkcheck/network

deb_orig:
	if [ ! -e $(DEB_ORIG_TARGET) ]; then \
	  cp dist/$(APPNAME)-$(VERSION).tar.xz $(DEB_ORIG_TARGET); \
	fi

release: distclean releasecheck filescheck clean dist-stamp sign_distfiles upload
	git tag v$(VERSION)
	$(MAKE) homepage
	$(MAKE) register
	$(MAKE) announce

homepage:
	@echo "Updating $(APPNAME) Homepage..."
	$(MAKE) -C doc man
	sed -i -e "s/version = '.*'/version = '$(VERSION)'/" ~/public_html/linkchecker.sf.net/source/conf.py
	$(MAKE) -C ~/public_html/linkchecker.sf.net update upload
	@echo "done."

register:
	@echo "Register at Python Package Index..."
	$(PYTHON) setup.py register
	@echo "done."

announce:
	@echo "Submitting to Freecode..."
	freecode-submit < $(LAPPNAME).freecode
	@echo "done."

chmod:
	-chmod -R a+rX,u+w,go-w $(CHMODMINUSMINUS) *
	find . -type d -exec chmod 755 {} \;

dist: locale MANIFEST chmod
	rm -f dist/$(APPNAME)-$(VERSION).tar.xz
	$(PYTHON) setup.py sdist --formats=tar
	xz dist/$(APPNAME)-$(VERSION).tar

dist-stamp: changelog config/ca-certificates.crt
	$(MAKE) dist
	touch $@

# Build OSX installer with py2app
app: distclean localbuild chmod
	$(PYTHON) setup.py py2app $(PY2APPOPTS)

# Build RPM installer with cx_Freeze
rpm:
	$(MAKE) -C doc/html
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py bdist_rpm

# The check programs used here are mostly local scripts on my private system.
# So for other developers there is no need to execute this target.
check:
	[ ! -d .svn ] || check-nosvneolstyle -v
	check-copyright
	check-pofiles -v
	py-tabdaddy
	py-unittest2-compat tests/
	$(MAKE) -C doc check
	$(MAKE) doccheck
	$(MAKE) pyflakes

doccheck:
	py-check-docstrings --force linkcheck/HtmlParser linkcheck/checker \
	  linkcheck/cache linkcheck/configuration linkcheck/director \
	  linkcheck/htmlutil linkcheck/logger linkcheck/network \
	  linkcheck/bookmarks \
	  linkcheck/gui/__init__.py \
	  linkcheck/gui/checker.py \
	  linkcheck/gui/contextmenu.py \
	  linkcheck/gui/debug.py \
	  linkcheck/gui/editor.py \
	  linkcheck/gui/editor_qsci.py \
	  linkcheck/gui/editor_qt.py \
	  linkcheck/gui/lineedit.py \
	  linkcheck/gui/help.py \
	  linkcheck/gui/logger.py \
	  linkcheck/gui/options.py \
	  linkcheck/gui/properties.py \
	  linkcheck/gui/settings.py \
	  linkcheck/gui/statistics.py \
	  linkcheck/gui/syntax.py \
	  linkcheck/gui/updater.py \
	  linkcheck/gui/urlmodel.py \
	  linkcheck/gui/urlsave.py \
	  $(filter-out %2.py,$(wildcard linkcheck/*.py)) \
	  cgi-bin/lc.wsgi \
	  linkchecker \
	  linkchecker-gui \
	  linkchecker-nagios \
	  *.py

filescheck: localbuild
	for out in text html gml sql csv xml gxml dot sitemap; do \
	  ./$(LAPPNAME) -o$$out -F$$out --complete -r1 -C $(FILESCHECK_URL) || exit 1; \
	done

update-copyright:
	update-copyright --holder="Bastian Kleineidam"

releasecheck: check
	@if egrep -i "xx\.|xxxx|\.xx" doc/changelog.txt > /dev/null; then \
	  echo "Could not release: edit doc/changelog.txt release date"; false; \
	fi
	@if ! grep "Version: $(VERSION)" $(LAPPNAME).freecode > /dev/null; then \
	  echo "Could not release: edit $(LAPPNAME).freecode version"; false; \
	fi
	@if grep "UNRELEASED" debian/changelog > /dev/null; then \
	  echo "Could not release: edit debian/changelog distribution name"; false; \
	fi
	$(PYTHON) setup.py check --restructuredtext

sign_distfiles:
	for f in $(shell find dist -name *.xz -o -name *.exe -o -name *.zip -o -name *.dmg); do \
	  [ -f $${f}.asc ] || gpg --detach-sign --armor $$f; \
	done

test:	localbuild
	env LANG=en_US.utf-8 $(PYTHON) -m pytest $(PYTESTOPTS) $(TESTOPTS) $(TESTS)

pyflakes:
	pyflakes $(PY_FILES_DIRS) 2>&1 | \
          grep -v -E "redefinition of unused '(StringIO|Editor|ContentTypeLexers|winreg)'" | \
          grep -v "local variable 'dummy' is assigned to but never used" | \
          grep -v -E "'(py2exe|py2app|PyQt4|biplist|setuptools|win32com|find_executable|parse_bookmark_data|parse_bookmark_file|wsgiref|pyftpdlib|linkchecker_rc)' imported but unused" | \
          grep -v -E "redefinition of unused '(setup|Distribution|build)'" | \
          grep -v "undefined name '_'" | \
	  grep -v "undefined name '_n'" | cat

pep8:
	pep8 $(PEP8OPTS) $(PY_FILES_DIRS)

# Compare custom Python files with the originals
diff:
	@for f in gzip robotparser httplib; do \
	  echo "Comparing $${f}.py"; \
	  diff -u linkcheck/$${f}2.py $(SRCDIR)/cpython.hg/Lib/$${f}.py | $(PAGER); \
	done
	@diff -u linkcheck/better_exchook.py $(SRCDIR)/py_better_exchook.git/better_exchook.py

# Compare dnspython files with the ones from upstream repository
dnsdiff:
	@(for d in dns tests; do \
	  diff -BurN --exclude=*.pyc third_party/dnspython/$$d $(DNSPYTHON)/$$d; \
	done) | $(PAGER)

changelog:
	github-changelog $(DRYRUN) $(GITUSER) $(GITREPO) doc/changelog.txt

gui:
	$(MAKE) -C linkcheck/gui

count:
	@sloccount linkchecker linkchecker-gui linkchecker-nagios linkcheck tests

# run eclipse ide
ide:
	eclipse -data $(CURDIR)/..

update-certificates:	config/ca-certificates.crt

config/ca-certificates.crt:	/etc/ssl/certs/ca-certificates.crt
	cp $< $@

.PHONY: test changelog gui count pyflakes ide login upload all clean distclean
.PHONY: pep8 cleandeb locale localbuild deb_orig diff dnsdiff sign_distfiles
.PHONY: filescheck update-copyright releasecheck check register announce
.PHONY: chmod dist app rpm release homepage update-certificates
