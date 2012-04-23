HTMLDIR:=$(HOME)/public_html/linkchecker.sf.net/source
MANFILES:= \
	$(HTMLDIR)/man1/linkchecker.1.html \
	$(HTMLDIR)/man5/linkcheckerrc.5.html \
	$(HTMLDIR)/man1/linkchecker-gui.1.html

all:

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

man:	$(MANFILES)

$(HTMLDIR)/man1/linkchecker.1.html: en/linkchecker.1 linkchecker.1.html.diff
	man2html -r $< | tail -n +2 | sed 's/Time:.*//g' | sed 's@/:@@g' > $@
	patch --no-backup-if-mismatch --quiet $@ linkchecker.1.html.diff

$(HTMLDIR)/man5/linkcheckerrc.5.html: en/linkcheckerrc.5 linkcheckerrc.5.html.diff
	man2html -r $< | tail -n +2 | sed 's/Time:.*//g' | sed 's@/:@@g' > $@
	patch --no-backup-if-mismatch --quiet $@ linkcheckerrc.5.html.diff

$(HTMLDIR)/man1/linkchecker-gui.1.html: en/linkchecker-gui.1 linkchecker-gui.1.html.diff
	man2html -r $< | tail -n +2 | sed 's/Time:.*//g' | sed 's@/:@@g' > $@
	patch --no-backup-if-mismatch --quiet $@ linkchecker-gui.1.html.diff

.PHONY: po4a man
