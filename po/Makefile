XGETTEXT := xgettext
MSGFMT := msgfmt
MSGMERGE := msgmerge
POSOURCES = $(shell find ../linkcheck -name \*.py) \
	../linkchecker
LDIR = ../share/locale
PACKAGE = linkchecker
TEMPLATE = $(PACKAGE).pot
LFILE = LC_MESSAGES/$(PACKAGE).mo
# defined language (add new languages here)
LANGUAGES = de fr nl

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
	  --copyright-holder="Bastian Kleineidam <calvin@users.sf.net>" \
	  --msgid-bugs-address=calvin@users.sf.net -o $(TEMPLATE) \
	  $(POSOURCES)

%.mo:	%.po
	if [ ! -d $(LDIR)/$*/LC_MESSAGES ]; then \
	  mkdir -p $(LDIR)/$*/LC_MESSAGES; \
	fi
	$(MSGFMT) -c --statistics -o $(LDIR)/$*/$(LFILE) $<

clean:
	@for f in $(LANGUAGES); do rm -f $(LDIR)/$$f/$(LFILE); done
	rm -f *.mo

.PHONY: mofiles clean
