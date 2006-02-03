# This Makefile is only used by developers.
PYVER := 2.4
PYTHON := python$(PYVER)
PACKAGE := linkchecker
VERSION := $(shell $(PYTHON) setup.py --version)
HOST=www.debian.org
LCOPTS=-Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -Fgxml -Fdot -v -r1 -t0 -C
PYFILES := $(wildcard linkcheck/*.py linkcheck/logger/*.py \
	linkcheck/checker/*.py)
TESTFILES := $(wildcard tests/*.py linkcheck/tests/*.py linkcheck/checker/tests/*.py)
CHECKFILES = *.py linkchecker scripts tests linkcheck config
PYLINT := env PYTHONPATH=. PYLINTRC=config/pylintrc pylint.$(PYTHON)
PYLINTOPTS := 
PYLINTIGNORE = linkcheck/httplib2.py
PYLINTFILES = $(filter-out $(PYLINTIGNORE),$(PYFILES))
PYFLAKES:=pyflakes
PYTHONSVN := /home/calvin/src/python-svn
.PHONY: all
all:
	@echo "Read the file doc/install.txt to see how to build and install this package."

.PHONY: clean
clean:
# ignore errors of this command
	-$(PYTHON) setup.py clean --all
	rm -f sign-stamp release-stamp
	$(MAKE) -C po clean
	rm -f linkcheck/HtmlParser/htmlsax.so
	rm -f linkcheck/HtmlParser/*.output
	find . -name '*.py[co]' -exec rm -f {} \;

.PHONY: distclean
distclean: clean cleandeb
# just to be sure clean also the build dir
	rm -rf dist build
	rm -f _$(PACKAGE)_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f $(PACKAGE)-out* $(PACKAGE).prof
	rm -rf $(PACKAGE)-$(VERSION)
	rm -rf coverage

.PHONY: cleandeb
cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
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
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py build
	cp -f build/lib.linux-i686-$(PYVER)/linkcheck/HtmlParser/htmlsax.so linkcheck/HtmlParser
	cp -f build/lib.linux-i686-$(PYVER)/linkcheck/ftpparse/_ftpparse.so linkcheck/ftpparse

# produce the .deb Debian package
.PHONY: deb_local
deb_local: cleandeb
# standard for local use
	fakeroot debian/rules binary

.PHONY: deb_signed
deb_signed: cleandeb
# ready for upload, signed with my GPG key
	env CVSROOT=:ext:calvin@cvs.linkchecker.sourceforge.net:/cvsroot/linkchecker cvs-buildpackage -Mlinkchecker -W/home/calvin/projects/cvs-build -sgpg -pgpg -k32EC6F3E -r"fakeroot --" -I.cvsignore

.PHONY: files
files:	locale localbuild
	-scripts/run.sh linkchecker $(LCOPTS) http://$(HOST)/
	rm -f linkchecker-out.*.gz
	for f in linkchecker-out.*; do gzip --best $$f; done

.PHONY: release
release: releasecheck distclean dist sign_distfiles homepage
	@echo "Starting releaseforge..."
	@releaseforge
	@echo "Uploading new LinkChecker Homepage..."
	$(MAKE) -C ~/public_html/linkchecker.sf.net upload
	@echo "Register at Python Package Index..."
	$(PYTHON) setup.py register

.PHONY: homepage
homepage:
	$(MAKE) -C doc/en homepage

.PHONY: dist
dist: locale MANIFEST
	$(PYTHON) setup.py sdist --formats=gztar bdist_rpm

.PHONY: releasecheck
releasecheck:
	@if egrep -i "xx\.|xxxx|\.xx" ChangeLog > /dev/null; then \
	  echo "Could not release: edit ChangeLog release date"; false; \
	fi

.PHONY: sign_distfiles
sign_distfiles:
	for f in dist/*; do \
	  if [ ! -f $${f}.asc ]; then \
	    gpg --detach-sign --armor $$f; \
	  fi; \
	done

.PHONY: check
check:	localbuild
	scripts/test.sh

.PHONY: pylint
pylint:
	$(PYLINT) $(PYLINTOPTS) $(PYLINTFILES) $(TESTFILES)

.PHONY: pyflakes
pyflakes:
	$(PYFLAKES) $(CHECKFILES) | \
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
	py-check-append $(CHECKFILES)
	py-clean-future -r $(CHECKFILES)
	py-find-nocoding $(CHECKFILES)
