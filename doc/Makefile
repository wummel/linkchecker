SUBDIRS = devel misc

RESTFILES = $(wildcard *.txt)
HTMLFILES = $(patsubst %.txt, %.html, $(RESTFILES) )
NAVFILES = $(patsubst %.txt, %.nav, $(RESTFILES) )
HTMLDIR := /home/calvin/public_html/linkchecker.sf.net

all: $(HTMLFILES)

%.html: %.txt htmlnav.py bfknav.py
	./rest2htmlnav --stylesheet-path=lc.css --time $< $@

nav: all
	python bfknav.py

apidocs:
#	epydoc --html -o devel/api --name "LinkChecker Development" --url ../../devel.html ../linkcheck ../test

homepage: nav apidocs
	cp *.html *.css *.jpg *.png $(HTMLDIR)/htdocs
	cp devel/*.html devel/*.diff $(HTMLDIR)/htdocs/devel
	cp misc/*.html $(HTMLDIR)/htdocs/misc
	cp -r devel/api $(HTMLDIR)/htdocs/devel


clean:
	rm -f $(NAVFILES) $(HTMLFILES) *.pyc *.pyo
