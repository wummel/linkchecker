# This Makefile is only used by developers.
# You will need a Debian Linux system to use this Makefile!
VERSION=$(shell python setup.py --version)
PACKAGE=linkchecker
NAME=$(shell python setup.py --name)
HOST=treasure.calvinsplayground.de
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -R -t0 -v -itreasure.calvinsplayground.de -s
DEBPACKAGE=$(PACKAGE)_$(VERSION)_i386.deb
I18NTOOLS=/usr/local/src/Python-2.0/Tools/i18n
GETTEXT=$(I18NTOOLS)/pygettext.py
MSGFMT=$(I18NTOOLS)/msgfmt.py
SOURCES=\
linkcheck/Config.py \
linkcheck/FileUrlData.py \
linkcheck/FtpUrlData.py \
linkcheck/GopherUrlData.py \
linkcheck/HostCheckingUrlData.py \
linkcheck/HttpUrlData.py \
linkcheck/HttpsUrlData.py \
linkcheck/JavascriptUrlData.py \
linkcheck/Logging.py \
linkcheck/MailtoUrlData.py \
linkcheck/NntpUrlData.py \
linkcheck/TelnetUrlData.py \
linkcheck/Threader.py \
linkcheck/UrlData.py \
linkcheck/__init__.py \
linkcheck/lc_cgi.py \
linkchecker

DESTDIR=/.
.PHONY: test clean files homepage dist install all

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
	fakeroot debian/rules clean

distclean:	clean
	rm -rf dist
	rm -f $(PACKAGE)-out.* VERSION

dist:	mo
	rm -rf debian/tmp
	python setup.py sdist --formats=gztar,zip bdist_rpm bdist_wininst
	fakeroot debian/rules binary
	mv -f ../$(DEBPACKAGE) dist

package:
	cd dist && dpkg-scanpackages . ../override.txt | gzip --best > Packages.gz

files:
	./$(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/~calvin/

VERSION:
	echo $(VERSION) > VERSION

upload: dist package files VERSION
	scp debian/changelog shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/changes.txt
	scp linkchecker-out.* shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs
	scp VERSION shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/raw/
	scp dist/* shell1.sourceforge.net:/home/groups/ftp/pub/$(PACKAGE)/
	ssh -C -t shell1.sourceforge.net "cd /home/groups/$(PACKAGE) && make"

test:
	rm -f test/*.result
	@for i in test/*.html; do \
	  echo "Testing $$i. Results are in $$i.result"; \
	  ./$(PACKAGE) -r1 -o text -N"news.rz.uni-sb.de" -v -a $$i > $$i.result 2>&1; \
        done

# we use pygettext.py in Tools/i18n of the Python distribution
po:
	# german translation
	$(GETTEXT) --default-domain=linkcheck --no-location \
	--output-dir=locale/de/LC_MESSAGES/ $(SOURCES)
	# french translation
	$(GETTEXT) --default-domain=linkcheck --no-location \
	--output-dir=locale/fr/LC_MESSAGES/ $(SOURCES)

mo:
	@for l in "de fr"; do \
	    (cd locale/$l/LC_MESSAGES && $(MSGFMT) linkcheck.po); \
	done
