# use scripts found in Tools/i18n of the Python distribution
GETTEXT := python pygettext.py
MSGFMT := msgfmt
MSGMERGE := msgmerge
POSOURCES = $(shell find ../linkcheck -name \*.py) \
	../linkchecker
LDIR = ../share/locale
PACKAGE = linkchecker
LFILE = LC_MESSAGES/$(PACKAGE).mo
# defined language (add new languages here)
LANGUAGES = de fr nl

mofiles:
	for la in $(LANGUAGES); do \
	  if [ ! -d $(LDIR)/$$la/LC_MESSAGES ]; then \
	    mkdir -p $(LDIR)/$$la/LC_MESSAGES; \
	  fi; \
	  $(MSGFMT) -o $(LDIR)/$$la/$(LFILE) $$l.po; \
	done

%.po:	$(PACKAGE).pot
	$(MSGMERGE) $@ $(PACKAGE).pot -o $@

$(PACKAGE).pot: $(SOURCES)
	$(GETTEXT) -w 80 --default-domain=$(PACKAGE) $(POSOURCES)

%.mo:	%.po
	if [ ! -d $(LDIR)/$*/LC_MESSAGES ]; then \
	  mkdir -p $(LDIR)/$*/LC_MESSAGES; \
	fi
	$(MSGFMT) -c --statistics -o $(LDIR)/$*/$(LFILE) $<

clean:
	for f in $(LANGUAGES); do rm -f $(LDIR)/$$f/$(LFILE); done

.PHONY: all clean
