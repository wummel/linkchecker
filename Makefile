# This Makefile is only used by developers.
PYVER:=2.7
PYTHON?=python$(PYVER)
VERSION:=$(shell $(PYTHON) setup.py --version)
PLATFORM:=$(shell $(PYTHON) -c "from __future__ import print_function; from distutils.util import get_platform; print(get_platform())")
APPNAME:=$(shell $(PYTHON) setup.py --name)
AUTHOR:=$(shell $(PYTHON) setup.py --author)
MAINTAINER:=$(shell $(PYTHON) setup.py --maintainer)
LAPPNAME:=$(shell echo $(APPNAME)|tr "[A-Z]" "[a-z]")
ARCHIVE_SOURCE_EXT:=gz
ARCHIVE_SOURCE:=$(APPNAME)-$(VERSION).tar.$(ARCHIVE_SOURCE_EXT)
ARCHIVE_WIN32:=$(APPNAME)-$(VERSION).exe
GITUSER:=wummel
GITREPO:=$(LAPPNAME)
HOMEPAGE:=$(HOME)/public_html/$(LAPPNAME)-webpage.git
WEB_META:=doc/web/app.yaml
DEBUILDDIR:=$(HOME)/projects/debian/official
DEBORIGFILE:=$(DEBUILDDIR)/$(LAPPNAME)_$(VERSION).orig.tar.$(ARCHIVE_SOURCE_EXT)
DEBPACKAGEDIR:=$(DEBUILDDIR)/$(APPNAME)-$(VERSION)
FILESCHECK_URL:=http://localhost/~calvin/
SRCDIR:=${HOME}/src
PY_FILES_DIRS:=linkcheck tests *.py linkchecker linkchecker-gui cgi-bin config doc/examples scripts
MYPY_FILES_DIRS:=linkcheck/HtmlParser linkcheck/checker \
	  linkcheck/cache linkcheck/configuration linkcheck/director \
	  linkcheck/htmlutil linkcheck/logger linkcheck/network \
	  linkcheck/bookmarks linkcheck/plugins linkcheck/parser \
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
	  *.py

TESTS ?= tests
# set test options, eg. to "--verbose"
TESTOPTS=
PAGER ?= less
# original dnspython repository module
DNSPYTHON:=$(HOME)/src/dnspython-git
# options to run the pep8 utility
PEP8OPTS:=--repeat --ignore=E211,E501,E225,E301,E302,E241 \
   --exclude="gzip2.py,httplib2.py,robotparser2.py"
PY2APPOPTS ?=
ifeq ($(shell uname),Darwin)
  CHMODMINUSMINUS:=
else
  CHMODMINUSMINUS:=--
endif
# Pytest options:
# - use multiple processes
# - write test results in file
PYTESTOPTS:=-n 4 --resultlog=testresults.txt


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

distclean: clean
	rm -rf build dist $(APPNAME).egg-info
	rm -f _$(APPNAME)_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f $(LAPPNAME)-out* $(LAPPNAME).prof
	rm -f alexa*.log testresults.txt
	rm -rf $(APPNAME)-$(VERSION)
	rm -rf coverage dist-stamp python-build-stamp*

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

release: distclean releasecheck filescheck
	$(MAKE) dist sign register upload homepage tag changelog deb

tag:
	git tag upstream/$(VERSION)
	git push --tags origin upstream/$(VERSION)

upload:	upload_source upload_binary

upload_source:
	twine upload dist/$(ARCHIVE_SOURCE) dist/$(ARCHIVE_SOURCE).asc

upload_binary:
	cp dist/$(ARCHIVE_WIN32) dist/$(ARCHIVE_WIN32).asc \
	  $(HOMEPAGE)/dist

homepage:
# update metadata
	@echo "version: \"$(VERSION)\"" > $(WEB_META)
	@echo "name: \"$(APPNAME)\"" >> $(WEB_META)
	@echo "lname: \"$(LAPPNAME)\"" >> $(WEB_META)
	@echo "maintainer: \"$(MAINTAINER)\"" >> $(WEB_META)
	@echo "author: \"$(AUTHOR)\"" >> $(WEB_META)
	git add $(WEBMETA)
	-git commit -m "Updated webpage meta info"
# update documentation and man pages
	$(MAKE) -C doc man
	$(MAKE) -C doc/web release

register:
	@echo "Register at Python Package Index..."
	$(PYTHON) setup.py register
	@echo "done."

deb:
# build a debian package
	[ -f $(DEBORIGFILE) ] || cp dist/$(ARCHIVE_SOURCE) $(DEBORIGFILE)
	sed -i -e 's/VERSION_$(LAPPNAME):=.*/VERSION_$(LAPPNAME):=$(VERSION)/' $(DEBUILDDIR)/$(LAPPNAME).mak
	[ -d $(DEBPACKAGEDIR) ] || (cd $(DEBUILDDIR); \
	  patool extract $(DEBORIGFILE); \
	  cd $(CURDIR); \
	  git checkout debian; \
	  cp -r debian $(DEBPACKAGEDIR); \
	  rm -f $(DEBPACKAGEDIR)/debian/.gitignore; \
	  git checkout master)
	$(MAKE) -C $(DEBUILDDIR) $(LAPPNAME)_clean $(LAPPNAME)

chmod:
	-chmod -R a+rX,u+w,go-w $(CHMODMINUSMINUS) *
	find . -type d -exec chmod 755 {} \;

dist: locale MANIFEST chmod
	rm -f dist/$(ARCHIVE_SOURCE)
	$(PYTHON) setup.py sdist --formats=tar
	gzip --best dist/$(APPNAME)-$(VERSION).tar
	[ ! -f ../$(ARCHIVE_WIN32) ] || cp ../$(ARCHIVE_WIN32) dist

# Build OSX installer with py2app
app: distclean localbuild chmod
	$(PYTHON) setup.py py2app $(PY2APPOPTS)

# Build RPM installer with cx_Freeze
rpm:
	$(MAKE) -C doc/html
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py bdist_rpm

# Build portable Linux app
binary:	distclean localbuild chmod
	LINKCHECKER_FREEZE=1 $(PYTHON) setup.py bdist

# The check programs used here are mostly local scripts on my private system.
# So for other developers there is no need to execute this target.
check:
	check-copyright
	check-pofiles -v
	py-tabdaddy $(MYPY_FILES_DIRS)
	py-unittest2-compat tests/
	$(MAKE) -C doc check
	$(MAKE) doccheck
	$(MAKE) pyflakes

doccheck:
	py-check-docstrings --force $(MYPY_FILES_DIRS)

filescheck: localbuild
	for out in text html gml sql csv xml gxml dot sitemap; do \
	  ./$(LAPPNAME) -o$$out -F$$out --complete -r1 -C $(FILESCHECK_URL) || exit 1; \
	done

update-copyright:
	update-copyright --holder="Bastian Kleineidam" $(PY_FILES_DIRS)

releasecheck: check
	@if egrep -i "xx\.|xxxx|\.xx" doc/changelog.txt > /dev/null; then \
	  echo "Could not release: edit doc/changelog.txt release date"; false; \
	fi
	@if [ ! -f ../$(ARCHIVE_WIN32) ]; then \
	  echo "Missing WIN32 distribution archive at ../$(ARCHIVE_WIN32)"; \
	  false; \
	fi
	$(PYTHON) setup.py check --restructuredtext

sign:
	for f in $(shell find dist -name *.$(ARCHIVE_SOURCE_EXT) -o -name *.exe -o -name *.zip -o -name *.dmg); do \
	  [ -f $${f}.asc ] || gpg --detach-sign --armor $$f; \
	done

test:	localbuild
	env LANG=en_US.utf-8 $(PYTHON) -m pytest $(PYTESTOPTS) $(TESTOPTS) $(TESTS)

pyflakes:
	pyflakes $(PY_FILES_DIRS) 2>&1 | \
          grep -v "local variable 'dummy' is assigned to but never used" | \
          grep -v -E "'(py2exe|py2app|PyQt4|biplist|setuptools|win32com|find_executable|parse_sitemap|parse_sitemapindex|parse_bookmark_data|parse_bookmark_file|wsgiref|pyftpdlib|linkchecker_rc)' imported but unused" | \
          grep -v "undefined name '_'" | \
	  grep -v "undefined name '_n'" | cat

pep8:
	pep8 $(PEP8OPTS) $(PY_FILES_DIRS)

# Compare custom Python files with the originals
diff:
	@for f in gzip robotparser; do \
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
	@sloccount linkchecker linkchecker-gui linkcheck tests

# run eclipse ide
ide:
	eclipse -data $(CURDIR)/..

.PHONY: test changelog gui count pyflakes ide login upload all clean distclean
.PHONY: pep8 cleandeb locale localbuild deb diff dnsdiff sign
.PHONY: filescheck update-copyright releasecheck check register announce
.PHONY: chmod dist app rpm release homepage
