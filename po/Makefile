# we copied the scripts in Tools/i18n of the Python 2.0 distribution
I18NTOOLS=.
PYTHON=python2.1
GETTEXT=$(PYTHON) $(I18NTOOLS)/pygettext.py
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
../linkcheck/Logging.py \
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
MOS=$(LDIR)/de/$(LFILE) $(LDIR)/fr/$(LFILE)
PACKAGE=linkcheck

.PHONY: all
all:
	$(MAKE) de.mo fr.mo

%.po:	.time.pot
	$(MSGMERGE) $@ $(PACKAGE).pot -o $@

.time.pot:
	rm -f $(PACKAGE).pot
	$(GETTEXT) --default-domain=$(PACKAGE) --no-location $(SOURCES)
	touch .time.pot

%.mo:	%.po
	$(MSGFMT) -o$(LDIR)/$*/$(LFILE) $<

clean:
	rm -f $(MOS)

distclean:	clean
	rm -f .time.pot

.PHONY: all clean distclean

