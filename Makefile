# This Makefile is only used by developers.
PYVER := 2.4
PYTHON := python$(PYVER)
VERSION := $(shell $(PYTHON) setup.py --version)
HOST=www.debian.org
LCOPTS=-Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -Fgxml -Fdot -v -r1 -C
# all Python files in the source
PYFILES = $(wildcard *.py) linkchecker linkcheck tests
PYFLAKES:=python$(PYVER) /usr/bin/pyflakes
PYTHONSVN := /home/calvin/src/python-svn
# build dir for svn-buildpackage
SVNBUILD:=/home/calvin/src/build-area
DEB_ORIG_TARGET:=$(SVNBUILD)/linkchecker_$(VERSION).orig.tar.gz


.PHONY: all
all:
	@echo "Read the file doc/install.txt to see how to build and install this package."

.PHONY: clean
clean:
# ignore errors of this command
	-$(PYTHON) setup.py clean --all
	rm -f sign-stamp release-stamp
	$(MAKE) -C po clean
	$(MAKE) -C doc clean
	$(MAKE) -C doc/en clean
	rm -f linkcheck/HtmlParser/htmlsax.so
	rm -f linkcheck/HtmlParser/*.output
	rm -f linkcheck/ftpparse/_ftpparse.so
	find . -name '*.py[co]' -exec rm -f {} \;

.PHONY: distclean
distclean: clean cleandeb
# just to be sure clean also the build dir
	rm -rf build
	rm -f _linkchecker_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f linkchecker-out* linkchecker.prof
	rm -rf linkchecker-$(VERSION)
	rm -rf coverage dist-stamp python-build-stamp*

.PHONY: cleandeb
cleandeb:
	rm -rf debian/linkchecker debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

MANIFEST: MANIFEST.in setup.py
	$(MAKE) -C doc/en all nav
	$(PYTHON) setup.py sdist --manifest-only

.PHONY: locale
locale:
	$(MAKE) -C po

# to build in the current directory
.PHONY: localbuild
localbuild: MANIFEST
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py build
	cp -f build/lib.linux-i686-$(PYVER)/linkcheck/HtmlParser/htmlsax.so linkcheck/HtmlParser
	cp -f build/lib.linux-i686-$(PYVER)/linkcheck/ftpparse/_ftpparse.so linkcheck/ftpparse

.PHONY: deb_orig
deb_orig:
	if [ ! -e $(DEB_ORIG_TARGET) ]; then \
	  $(MAKE) dist-stamp && \
	  cp dist/linkchecker-$(VERSION).tar.gz $(DEB_ORIG_TARGET); \
	fi

# ready for upload, signed with my GPG key
.PHONY: deb_signed
deb_signed: cleandeb
	(env -u LANG svn-buildpackage --svn-dont-clean --svn-verbose --svn-ignore \
	  --svn-prebuild="$(MAKE) deb_orig" --svn-lintian --svn-linda \
	  -sgpg -pgpg -k$(GPGKEY) -r"fakeroot --" 2>&1) | \
	tee $(SVNBUILD)/linkchecker-$(VERSION).build

.PHONY: files
files:	locale localbuild
	-scripts/run.sh linkchecker $(LCOPTS) http://$(HOST)/
	rm -f linkchecker-out.*.gz
	for f in linkchecker-out.*; do gzip --best $$f; done

.PHONY: upload
upload:
	@echo "Starting releaseforge..."
	@releaseforge
#	ncftpput upload.sourceforge.net /incoming dist/*
#	mozilla -remote "openUrl(https://sourceforge.net/projects/linkchecker, new-tab)"
#	@echo "Make SF release and press return..."
#	@read

.PHONY: release
release: distclean releasecheck dist-stamp sign_distfiles homepage upload
	@echo "Uploading new LinkChecker Homepage..."
	$(MAKE) -C ~/public_html/linkchecker.sf.net upload
	@echo "Register at Python Package Index..."
	$(PYTHON) setup.py register

.PHONY: homepage
homepage:
	$(MAKE) -C doc/en homepage

.PHONY: chmod
chmod:
	-chmod -R a+rX,u+w,go-w -- *
	find . -type d -exec chmod 755 {} \;

.PHONY: dist
dist: locale MANIFEST chmod
	$(PYTHON) setup.py sdist --formats=gztar bdist_rpm

dist-stamp:
	$(MAKE) dist
	touch $@

.PHONY: syntaxcheck
syntaxcheck:
	py-verify

.PHONY: releasecheck
releasecheck: syntaxcheck
	@if egrep -i "xx\.|xxxx|\.xx" ChangeLog > /dev/null; then \
	  echo "Could not release: edit ChangeLog release date"; false; \
	fi
	$(MAKE) -C doc/en test

.PHONY: sign_distfiles
sign_distfiles:
	for f in dist/*; do \
	  if [ ! -f $${f}.asc ]; then \
	    gpg --detach-sign --armor $$f; \
	  fi; \
	done

.PHONY: test
test:	localbuild
	scripts/test.sh

.PHONY: pyflakes
pyflakes:
	$(PYFLAKES) $(PYFILES) | \
          grep -v "redefinition of unused 'linkcheck'" | \
          grep -v "undefined name '_'" | \
	  grep -v "undefined name '_n'"

.PHONY: reindent
reindent:
	$(PYTHON) config/reindent.py -r -v linkcheck

# Compare custom Python files with the original ones from subversion.
.PHONY: diff
diff:
	@for f in gzip robotparser httplib; do \
	  echo "Comparing $${f}.py"; \
	  diff -u linkcheck/$${f}2.py $(PYTHONSVN)/Lib/$${f}.py | less; \
	done

# various python check scripts
.PHONY: various
various:
	py-check-append $(PYFILES)
	py-clean-future -r $(PYFILES)
	py-find-nocoding $(PYFILES)
