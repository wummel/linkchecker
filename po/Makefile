XGETTEXT := xgettext
MSGFMT := msgfmt
MSGMERGE := msgmerge
POSOURCES = $(shell find ../linkcheck -name \*.py) \
	../linkchecker /usr/lib/python2.7/argparse.py
LDIR = ../share/locale
PACKAGE = linkchecker
TEMPLATE = $(PACKAGE).pot
MYMAIL := bastian.kleineidam@web.de
LFILE = LC_MESSAGES/$(PACKAGE).mo
# defined language (add new languages here)
LANGUAGES = de fr es
MOFILES = $(wildcard *.po)

all:	$(MOFILES)

%.mo:	%.po
	$(MSGFMT) -c --statistics -o $@ $<

%.po:	$(TEMPLATE)
	$(MSGMERGE) -U --suffix=.bak $@ $<

template: $(TEMPLATE)
$(TEMPLATE): $(POSOURCES)
	$(XGETTEXT) -w 80 --default-domain=$(PACKAGE) --language=Python \
	  --copyright-holder="Bastian Kleineidam <$(MYMAIL)>" \
	  --msgid-bugs-address=$(MYMAIL) -o $(TEMPLATE) \
	  --keyword=_n:1,2 $(POSOURCES)

%.mo:	%.po
	if [ ! -d $(LDIR)/$*/LC_MESSAGES ]; then \
	  mkdir -p $(LDIR)/$*/LC_MESSAGES; \
	fi
	$(MSGFMT) -c --statistics -o $(LDIR)/$*/$(LFILE) $<

clean:
	@for f in $(LANGUAGES); do rm -f $(LDIR)/$$f/$(LFILE); done
	rm -f *.mo *.bak

.PHONY: clean
