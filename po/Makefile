XGETTEXT := xgettext
MSGFMT := msgfmt
MSGMERGE := msgmerge
POSOURCES = $(shell find ../linkcheck -name \*.py) \
	../linkchecker ../linkchecker-gui /usr/lib/python2.7/argparse.py
LDIR = ../share/locale
PACKAGE = linkchecker
TEMPLATE = $(PACKAGE).pot
MYMAIL := bastian.kleineidam@web.de
LFILE = LC_MESSAGES/$(PACKAGE).mo
# defined language (add new languages here)
LANGUAGES = de fr es

all:

mofiles:
	@for la in $(LANGUAGES); do \
	  if [ ! -d $(LDIR)/$$la/LC_MESSAGES ]; then \
	    mkdir -p $(LDIR)/$$la/LC_MESSAGES; \
	  fi; \
	  echo "Formatting language catalog $${la}:"; \
	  $(MSGFMT) -c --statistics -o $(LDIR)/$$la/$(LFILE) $$la.po; \
	done

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

.PHONY: mofiles clean
