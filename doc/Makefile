# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         = a4

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source

.PHONY: help clean html web pickle htmlhelp latex changes linkcheck

all:
	@echo "Available targets: build-html build-htmlhelp"

build-html:	clean html

build-htmlhelp:	clean htmlhelp helpfiles

html:
	mkdir -p build/html build/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) build/html
	rm build/html/_static/Makefile
	rm build/html/_static/default.css
	rm build/html/_static/*.js
	rm build/html/_static/contents.png
	rm build/html/_static/plus.png
	rm build/html/_static/file.png
	rm build/html/_static/minus.png
	rm build/html/_static/navigation.png
	rm build/html/_static/rightsidebar.css
	rm build/html/_static/stickysidebar.css
	rm build/html/_static/sphinxdoc.css
	rm build/html/_static/traditional.css
	@echo
	@echo "Build finished. The HTML pages are in build/html."

htmlhelp:
	mkdir -p build/htmlhelp build/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) build/htmlhelp
	rm build/htmlhelp/LinkChecker*
	rm build/htmlhelp/_static/Makefile
	rm build/htmlhelp/_static/default.css
	rm build/htmlhelp/_static/*.js
	rm build/htmlhelp/_static/contents.png
	rm build/htmlhelp/_static/plus.png
	rm build/htmlhelp/_static/file.png
	rm build/htmlhelp/_static/minus.png
	rm build/htmlhelp/_static/navigation.png
	rm build/htmlhelp/_static/rightsidebar.css
	rm build/htmlhelp/_static/stickysidebar.css
	rm build/htmlhelp/_static/sphinxdoc.css
	rm build/htmlhelp/_static/traditional.css
	@echo
	@echo "Build finished. The HTML pages are in build/htmlhelp."

pickle:
	mkdir -p build/pickle build/doctrees
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) build/pickle
	@echo
	@echo "Build finished; now you can process the pickle files."

web: pickle

json:
	mkdir -p build/json build/doctrees
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) build/json
	@echo
	@echo "Build finished; now you can process the JSON files."

latex:
	mkdir -p build/latex build/doctrees
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) build/latex
	@echo
	@echo "Build finished; the LaTeX files are in build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	mkdir -p build/changes build/doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) build/changes
	@echo
	@echo "The overview file is in build/changes."

linkcheck:
	mkdir -p build/linkcheck build/doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in build/linkcheck/output.txt."

clean:
	-rm -rf build/*
	-rm -f *.qhc *.qch

test:	html
	xmllint --valid --noout build/html/*.html

YUICOMP_VERSION=2.4.2
YUICOMP=$(HOME)/src/yuicompressor-$(YUICOMP_VERSION)/build

compress:
	python mediacompress.py --overwrite=png,jpg,gif,js,css \
	  --js-compressor=$(YUICOMP)/yuicompressor-$(YUICOMP_VERSION).jar \
	  build


HELPFILES = lccollection.qhc

helpfiles: $(HELPFILES)

%.qhc:	%.qhcp lcdoc.qhp
	qcollectiongenerator $< -o $@


homepage:	build-html compress
	cp -r build/html/* $(HOME)/public_html/linkchecker.sf.net/htdocs

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

api:
	epydoc --html -o api --name "LinkChecker source documentation" --url ../index.html ../linkcheck/
