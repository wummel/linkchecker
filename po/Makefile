# we copied the scripts in Tools/i18n of the Python 2.0 distribution
I18NTOOLS=.
PYTHON=python2.0
GETTEXT=$(PYTHON) $(I18NTOOLS)/pygettext.py
MSGFMT=$(PYTHON) $(I18NTOOLS)/msgfmt.py
#MSGFMT=msgfmt
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

# for GNU msgfmt use -o flag:
#$(MSGFMT) $< -o $@ && mkdir -p ../locale/$*/LC_MESSAGES && mv $@ ../locale/$*/LC_MESSAGES/$(PACKAGE).mo
%.mo:	%.po
	$(MSGFMT) $< && mkdir -p ../locale/$*/LC_MESSAGES && mv $@ ../locale/$*/LC_MESSAGES/$(PACKAGE).mo

clean:
	rm -f .time.pot
	rm -rf ../locale
