# we use the scripts in Tools/i18n of the Python 2.3 distribution
PYTHON=python2.2
I18NTOOLS=.
GETTEXT=$(PYTHON) $(I18NTOOLS)/pygettext.py -k i18n._
MSGFMT=$(PYTHON) $(I18NTOOLS)/msgfmt.py
#MSGFMT=msgfmt
MSGMERGE=msgmerge
SOURCES=\
../linkcheck/AnsiColor.py \
../linkcheck/Config.py \
../linkcheck/FileUrlData.py \
../linkcheck/FtpUrlData.py \
../linkcheck/GopherUrlData.py \
../linkcheck/HostCheckingUrlData.py \
../linkcheck/HttpUrlData.py \
../linkcheck/HttpsUrlData.py \
../linkcheck/IgnoredUrlData.py \
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
../linkcheck/ProxyUrlData.py \
../linkcheck/StringUtil.py \
../linkcheck/TelnetUrlData.py \
../linkcheck/Threader.py \
../linkcheck/UrlData.py \
../linkcheck/__init__.py \
../linkcheck/debug.py \
../linkcheck/i18n.py \
../linkcheck/lc_cgi.py \
../linkcheck/linkname.py \
../linkcheck/linkparse.py \
../linkchecker

LDIR=../share/locale
LFILE=LC_MESSAGES/$(PACKAGE).mo
PACKAGE=linkcheck
# defined language (add new languages here)
LANGUAGES=de fr nl
MOS=$(patsubst %, %.mo, $(LANGUAGES) )

all:	$(MOS)

%.po:	pot-stamp
	$(MSGMERGE) $@ $(PACKAGE).pot -o $@

pot-stamp: $(SOURCES)
	rm -f $(PACKAGE).pot
	$(GETTEXT) --default-domain=$(PACKAGE) --no-location $(SOURCES)
	touch pot-stamp

%.mo:	%.po
	if [ ! -d $(LDIR)/$*/LC_MESSAGES ]; then \
	  mkdir -p $(LDIR)/$*/LC_MESSAGES; \
	fi
	$(MSGFMT) -o$(LDIR)/$*/$(LFILE) $<

clean:
	for f in $(LANGUAGES); do rm -f $(LDIR)/$$f/$(LFILE); done

distclean:	clean
	rm -f pot-stamp

.PHONY: all clean distclean
