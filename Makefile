# Makefile for Sphinx documentation

# You can set these variables from the command line.
SPHINXOPTS =
SPHINXBUILD = sphinx-build

.PHONY: all gen html test upload

all: gen

include ../chmod.mak

gen: html compress chmod

html:
	$(SPHINXBUILD) -b html $(SPHINXOPTS) source .
	-rm _static/Makefile
	-rm _static/default.css
	-rm _static/plus.png
	-rm _static/minus.png
	cp -r source/man1 source/man5 .
	@echo
	@echo "Build finished."

test:	html
	xmllint --valid --noout *.html

compress:
	python $(HOME)/src/mediacompress.py --overwrite=png,jpg,gif,js,css _images _static

upload:
	git add .
	git commit -m "Updated."
	git push
