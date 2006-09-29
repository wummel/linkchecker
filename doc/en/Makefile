RESTFILES = $(wildcard *.txt)
HTMLFILES = $(patsubst %.txt, %.html, $(RESTFILES) )
NAVFILES = $(patsubst %.txt, %.nav, $(RESTFILES) )
HTMLDIR := /home/calvin/public_html/linkchecker.sf.net

all: $(HTMLFILES)

.PHONY: clean
clean:
	rm -f $(HTMLFILES) $(NAVFILES)

%.html:	%.txt ../htmlnav.py ../bfknav.py lc.css
	../rest2htmlnav --stylesheet-path=lc.css --time $< $@

.PHONY: nav
nav: all
	python2.4 ../bfknav.py

.PHONY: homepage
homepage: nav
	cp *.html *.css *.jpg *.png *.ico $(HTMLDIR)/htdocs

.PHONY: test
test:	all
	xmllint --valid --noout *.html
