HTMLDIR:=$(HOME)/public_html/linkchecker.sf.net/source
MANFILES:= \
	$(HTMLDIR)/man1/linkchecker.1.html \
	$(HTMLDIR)/man5/linkcheckerrc.5.html \
	$(HTMLDIR)/man1/linkchecker-gui.1.html

all:

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

man:	$(MANFILES)

$(HTMLDIR)/man1/linkchecker.1.html: en/linkchecker.1
	man2html -r $< | tail -n +2 > $@

$(HTMLDIR)/man5/linkcheckerrc.5.html: en/linkcheckerrc.5
	man2html -r $< | tail -n +2 > $@

$(HTMLDIR)/man1/linkchecker-gui.1.html: en/linkchecker-gui.1
	man2html -r $< | tail -n +2 > $@

.PHONY: po4a man
