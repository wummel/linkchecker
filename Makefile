VERSION=$(shell ./setup.py -V)
HOST=treasure.calvinsplayground.de
PROXY=-P$(HOST):5050
#HOST=fsinfo.cs.uni-sb.de
#PROXY=-Pwww-proxy.uni-sb.de:3128
PACKAGE = linkchecker
DEBPACKAGE = $(PACKAGE)_$(VERSION)_i386.deb
ALLPACKAGES = ../$(DEBPACKAGE)
DESTDIR=/.
.PHONY: test clean files homepage dist install all
TAR = tar
ZIP = zip

all:

clean:
	./setup.py clean --all
	rm -rf $(ALLPACKAGES) $(PACKAGE)-out.*

install:
	./setup.py install --destdir=$(DESTDIR)
	install -c 644 linkcheckerrc $(DESTDIR)/etc

dist:
	./setup.py sdist
	fakeroot debian/rules binary
        
files:
	./$(PACKAGE) -Wtext -Whtml -Wgml -Wsql -R -t0 -v $(PROXY) -i$(HOST) http://$(HOST)/~calvin/

homepage:	files
	scp *-out.* shell1.sourceforge.net:/home/groups/linkchecker/htdocs/
	scp ChangeLog shell1.sourceforge.net:/home/groups/linkchecker/htdocs/changes.txt

test:
	rm -f test/*.result
	@for i in test/*.html; do \
	  echo "Testing $$i. Results are in $$i.result"; \
	  ./$(PACKAGE) -t0 -v -a $$i > $$i.result 2>&1; \
        done
