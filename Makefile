# This Makefile is only used by developers! No need for users to
# call make.
VERSION=$(shell python setup.py --version)
HOST=treasure.calvinsplayground.de
PROXY=--proxy= -itreasure.calvinsplayground.de -s
#PROXY=-P$(HOST):5050
#HOST=fsinfo.cs.uni-sb.de
#PROXY=-Pwww-proxy.uni-sb.de:3128
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -R -t0 -v
PACKAGE = linkchecker
DEBPACKAGE = ../$(PACKAGE)_$(VERSION)_i386.deb
RPMPATH=build/bdist.linux2-i686/rpm
RPMPACKAGE=$(RPMPATH)/RPMS/i386/$(PACKAGE)-$(VERSION)-1.i386.rpm
SRPMPACKAGE=$(RPMPATH)/SRPMS/$(PACKAGE)-$(VERSION)-1.src.rpm
ALLPACKAGES = $(DEBPACKAGE) $(RPMPACKAGE) $(SRPMPACKAGE)
SOURCES = linkcheck/Config.py \
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
linkcheck/RobotsTxt.py \
linkcheck/TelnetUrlData.py \
linkcheck/Threader.py \
linkcheck/UrlData.py \
linkcheck/__init__.py.tmpl \
linkchecker

DESTDIR=/.
.PHONY: test clean files homepage dist install all
TAR = tar
ZIP = zip

all:
	@echo "run python setup.py --help to see how to build and install"

clean:
	python setup.py clean --all
	rm -rf $(ALLPACKAGES) $(PACKAGE)-out.*

dist:
	python setup.py sdist bdist_rpm
	fakeroot debian/rules binary

files:
	./$(PACKAGE) $(LCOPTS) $(PROXY) -i$(HOST) http://$(HOST)/~calvin/

upload:
	scp debian/changelog shell1.sourceforge.net:/home/groups/linkchecker/htdocs/changes.txt
	ncftpput download.sourceforge.net /incoming $(ALLPACKAGES)

test:
	rm -f test/*.result
	@for i in test/*.html; do \
	  echo "Testing $$i. Results are in $$i.result"; \
	  ./$(PACKAGE) -r1 -o text -t0 -N"news.rz.uni-sb.de" -v -a $$i > $$i.result 2>&1; \
        done

po:
	# german translation
	xgettext --default-domain=linkcheck \
	--join-existing --keyword --keyword=_ \
	--output-dir=locale/de/LC_MESSAGES/ --sort-output $(SOURCES)
	# french translation
	xgettext --default-domain=linkcheck \
	--join-existing --keyword --keyword=_ \
	--output-dir=locale/fr/LC_MESSAGES/ --sort-output $(SOURCES)

mo:
	# german translation
	msgfmt -o locale/de/LC_MESSAGES/linkcheck.mo \
	locale/de/LC_MESSAGES/linkcheck.po
	# french translation
	msgfmt -o locale/fr/LC_MESSAGES/linkcheck.mo \
	locale/fr/LC_MESSAGES/linkcheck.po
