# we use the scripts in Tools/i18n of the Python 2.3 distribution
PYTHON := python2.3
I18NTOOLS := .
GETTEXT := $(PYTHON) $(I18NTOOLS)/pygettext.py -k i18n._
#MSGFMT := $(PYTHON) $(I18NTOOLS)/msgfmt.py
MSGFMT := msgfmt -c
MSGMERGE := msgmerge
SOURCES = $(shell find ../linkcheck -name \*.py) \
../linkchecker

LDIR = ../share/locale
PACKAGE = linkcheck
LFILE = LC_MESSAGES/$(PACKAGE).mo
# defined language (add new languages here)
LANGUAGES = de fr nl
MOS = $(patsubst %, %.mo, $(LANGUAGES) )

all:	$(MOS)

win:
	@for l in $(LANGUAGES); do \
	  if [ ! -d $(LDIR)/$$l/LC_MESSAGES ]; then \
	    mkdir -p $(LDIR)/$$l/LC_MESSAGES; \
	  fi; \
	  $(MSGFMT) -o$(LDIR)/$$l/$(LFILE) $$l.po; \
	done

%.po:	$(PACKAGE).pot
	$(MSGMERGE) $@ $(PACKAGE).pot -o $@

$(PACKAGE).pot: $(SOURCES)
	$(GETTEXT) --default-domain=$(PACKAGE) --no-location $(SOURCES)

%.mo:	%.po
	if [ ! -d $(LDIR)/$*/LC_MESSAGES ]; then \
	  mkdir -p $(LDIR)/$*/LC_MESSAGES; \
	fi
	$(MSGFMT) -o$(LDIR)/$*/$(LFILE) $<

clean:
	for f in $(LANGUAGES); do rm -f $(LDIR)/$$f/$(LFILE); done

.PHONY: all clean
