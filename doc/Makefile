HTMLDIR:=web/media
MANHTMLFILES:= \
	$(HTMLDIR)/man1/linkchecker.1.html \
	$(HTMLDIR)/man5/linkcheckerrc.5.html

MANFILES:=linkchecker.1 linkcheckerrc.5
LOCALES:=en de

all:

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

man:	$(MANHTMLFILES)

$(HTMLDIR)/man1/linkchecker.1.html: en/linkchecker.1 linkchecker.1.html.diff
	man2html -r $< | tail -n +2 | sed 's/Time:.*//g' | sed 's@/:@/@g' > $@
	patch --no-backup-if-mismatch --quiet $@ linkchecker.1.html.diff

$(HTMLDIR)/man5/linkcheckerrc.5.html: en/linkcheckerrc.5 linkcheckerrc.5.html.diff
	man2html -r $< | tail -n +2 | sed 's/Time:.*//g' | sed 's@/:@/@g' > $@
	patch --no-backup-if-mismatch --quiet $@ linkcheckerrc.5.html.diff

# check all makefiles for formatting warnings
check:
	@t=$(shell tempfile); \
	for loc in $(LOCALES); do \
	  for manfile in $(MANFILES); do \
	    echo "Checking $$loc/$$manfile"; \
	    LC_ALL=en_US.UTF-8 MANWIDTH=80 man --warnings -E UTF-8 -l $$loc/$$manfile > /dev/null 2>$$t ; \
	    if [ -s $$t ]; then cat $$t; exit 1; fi; \
	  done; \
	done

.PHONY: po4a man check
