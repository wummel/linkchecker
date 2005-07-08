RESTFILES = $(wildcard *.txt)
HTMLFILES = $(patsubst %.txt, %.html, $(RESTFILES) )
NAVFILES = $(patsubst %.txt, %.nav, $(RESTFILES) )
HTMLDIR := /home/calvin/public_html/linkchecker.sf.net

all: $(HTMLFILES)

%.html:	%.txt ../htmlnav.py ../bfknav.py
	../rest2htmlnav --stylesheet-path=lc.css --time $< $@

nav: all
	python2.4 ../bfknav.py

homepage: nav
	cp *.html *.css *.jpg *.png *.ico $(HTMLDIR)/htdocs

