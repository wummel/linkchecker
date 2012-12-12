HELPFILES := lccollection.qhc
HTMLFILES := index.html
OXYGEN := ${HOME}/src/oxygen-gitsvn
ICOICONS := logo16x16.png logo32x32.png
ICNSICONS := logo16x16.png logo32x32.png logo48x48.png logo128x128.png

all:	$(HELPFILES) $(HTMLFILES)

clean:
	-rm -f *.qhc *.qch

%.html:	%.txt html.header html.footer
	(cat html.header; markdown2 $<; cat html.footer) > $@

test:
	xmllint --valid --noout $(HTMLFILES)

%.qhc:	%.qhcp lcdoc.qhp $(HTMLFILES)
	qcollectiongenerator $< -o $@

logo%.png:	$(OXYGEN)/%/categories/applications-development-web.png
	cp $< $@

favicon.ico:	$(ICOICONS)
	png2ico favicon.ico $(ICOICONS)

favicon.icns:	$(ICNSICONS)
	png2icns favicon.icns $(ICNSICONS)

.PHONY: clean test
