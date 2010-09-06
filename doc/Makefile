HTMLDIR:=$(HOME)/public_html/linkchecker.sf.net/source

all:

test:
	xmllint --valid --noout *.html

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

api:
	epydoc --html -o api --name "LinkChecker source documentation" --url ../index.html ../linkcheck/

homepage:
	man2html -r en/linkchecker.1 | tail -n +2 > $(HTMLDIR)/man1/linkchecker.1.html
	man2html -r en/linkcheckerrc.5 | tail -n +2 > $(HTMLDIR)/man5/linkcheckerrc.5.html
	man2html -r en/linkchecker-gui.1 | tail -n +2 > $(HTMLDIR)/man1/linkchecker-gui.1.html

.PHONY: po4a api test homepage
