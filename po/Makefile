# I copied the scripts in Tools/i18n of the Python 2.0 distribution
I18NTOOLS=.
PYTHON=python
GETTEXT=$(PYTHON) $(I18NTOOLS)/pygettext.py -k linkcheck._
MSGFMT=$(PYTHON) $(I18NTOOLS)/msgfmt.py
#MSGFMT=msgfmt
MSGMERGE=msgmerge
SOURCES=\
../linkcheck/Config.py \
../linkcheck/FileUrlData.py \
../linkcheck/IgnoredUrlData.py \
../linkcheck/FtpUrlData.py \
../linkcheck/GopherUrlData.py \
../linkcheck/HostCheckingUrlData.py \
../linkcheck/HttpUrlData.py \
../linkcheck/HttpsUrlData.py \
../linkcheck/log/__init__.py \
../linkcheck/log/Logger.py \
../linkcheck/log/BlacklistLogger.py \
../linkcheck/log/CSVLogger.py \
../linkcheck/log/ColoredLogger.py \
../linkcheck/log/GMLLogger.py \
../linkcheck/log/HtmlLogger.py \
../linkcheck/log/SQLLogger.py \
../linkcheck/log/StandardLogger.py \
../linkcheck/log/XMLLogger.py \
../linkcheck/MailtoUrlData.py \
../linkcheck/NntpUrlData.py \
../linkcheck/TelnetUrlData.py \
../linkcheck/Threader.py \
../linkcheck/UrlData.py \
../linkcheck/__init__.py \
../linkcheck/lc_cgi.py \
../linkchecker
LDIR=../share/locale
LFILE=LC_MESSAGES/$(PACKAGE).mo
PACKAGE=linkcheck
# defined language (add new languages here)
LANGUAGES=de fr nl
MOS=$(patsubst %, %.mo, $(LANGUAGES) )

.PHONY: all
all:	$(MOS)

%.po:	.time.pot
	$(MSGMERGE) $@ $(PACKAGE).pot -o $@

.time.pot:
	rm -f $(PACKAGE).pot
	$(GETTEXT) --default-domain=$(PACKAGE) --no-location $(SOURCES)
	touch .time.pot

%.mo:	%.po
	if [ ! -d $(LDIR)/$*/LC_MESSAGES ]; then \
	  mkdir -p $(LDIR)/$*/LC_MESSAGES; \
	fi
	$(MSGFMT) -o$(LDIR)/$*/$(LFILE) $<

clean:
	for f in $(LANGUAGES); do rm -f $(LDIR)/$$f/$(LFILE); done

distclean:	clean
	rm -f .time.pot

.PHONY: all clean distclean

