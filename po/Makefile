# we use the scripts in Tools/i18n of the Python 2.0 distribution
I18NTOOLS=.
GETTEXT=python $(I18NTOOLS)/pygettext.py
MSGFMT=python $(I18NTOOLS)/msgfmt.py
MSGMERGE=msgmerge
SOURCES=\
../linkcheck/Config.py \
../linkcheck/FileUrlData.py \
../linkcheck/FtpUrlData.py \
../linkcheck/GopherUrlData.py \
../linkcheck/HostCheckingUrlData.py \
../linkcheck/HttpUrlData.py \
../linkcheck/HttpsUrlData.py \
../linkcheck/JavascriptUrlData.py \
../linkcheck/Logging.py \
../linkcheck/MailtoUrlData.py \
../linkcheck/NntpUrlData.py \
../linkcheck/TelnetUrlData.py \
../linkcheck/Threader.py \
../linkcheck/UrlData.py \
../linkcheck/__init__.py \
../linkcheck/lc_cgi.py \
../linkchecker
TARGETS=de.mo fr.mo
PACKAGE=linkcheck

all:
	$(MAKE) $(TARGETS)

%.po:	.time.pot
	$(MSGMERGE) $@ $(PACKAGE).pot -o $@

.time.pot:
	rm -f $(PACKAGE).pot
	$(GETTEXT) --default-domain=$(PACKAGE) --no-location $(SOURCES)
	touch .time.pot

%.mo:	%.po
	$(MSGFMT) $< && mv $@ ../locale/$*/LC_MESSAGES/$(PACKAGE).mo
	
clean:
	rm -f .time.pot
