PY_INCLDIR = -I/usr/include/python1.5
PY_LIBDIR = -L/usr/lib
SSL_INCLDIR = -I/usr/include/openssl
SSL_LIBDIR = -L/usr/lib

CC = gcc
CFLAGS = -O6 -Wall
LDFLAGS = -shared $(SSL_LIBDIR) $(PY_LIBDIR)
CPPFLAGS = $(SSL_INCLDIR) $(PY_INCLDIR)

VERSION=1.1.1
#HOST=treasure.calvinsplayground.de
HOST=fsinfo.cs.uni-sb.de
PACKAGE = linkchecker
BZ2PACKAGE = $(PACKAGE)-$(VERSION).tar.bz2
DEBPACKAGE = $(PACKAGE)_$(VERSION)_i386.deb
ZIPPACKAGE = $(PACKAGE)-$(VERSION).zip
ALLPACKAGES = ../$(BZ2PACKAGE) ../$(DEBPACKAGE) ../$(ZIPPACKAGE)
.PHONY: test clean files install all
TAR = tar
ZIP = zip

all:	ssl.so

ssl.so:	ssl.o
	$(CC) $(LDFLAGS) -o $@ $? -lssl -lcrypto -lpython1.5

clean:
	rm -f ssl.{so,o} $(ALLPACKAGES) $(PACKAGE)-out.*

files: all
	./$(PACKAGE) -q -Wtext -Whtml -Wgml -Wsql -R -r2 -v -i "$(HOST)" http://$(HOST)/~calvin/

install:	install-dirs
	install -m644 linkcheck/*.py? $(DESTDIR)/usr/share/$(PACKAGE)/linkcheck
	install -m644 DNS/*.py? $(DESTDIR)/usr/share/$(PACKAGE)/DNS
	install -m644 ssl.so *.py? $(DESTDIR)/usr/share/$(PACKAGE)
	install -m755 $(PACKAGE) $(DESTDIR)/usr/bin
	install -m644 $(PACKAGE)rc $(DESTDIR)/etc
	
install-dirs:
	install -d -m755 \
	$(DESTDIR)/usr/share/$(PACKAGE)/linkcheck \
	$(DESTDIR)/usr/share/$(PACKAGE)/DNS \
	$(DESTDIR)/usr/bin \
	$(DESTDIR)/etc

dist:	files
	dh_clean
	cd .. && $(TAR) cIhf $(BZ2PACKAGE) $(PACKAGE)
	cd .. && $(ZIP) -r $(ZIPPACKAGE) $(PACKAGE)
	fakeroot debian/rules binary

package:
	cd .. && $(TAR) cIhf $(BZ2PACKAGE) $(PACKAGE)

test:
	rm -f test/*.result
	@for i in test/*.html; do \
	  echo "Testing $$i. Results are in $$i.result"; \
	  ./$(PACKAGE) -t0 -v -a $$i > $$i.result 2>&1; \
        done
        
