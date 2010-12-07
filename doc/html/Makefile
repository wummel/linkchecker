HELPFILES = lccollection.qhc
HTMLFILES = index.html options.html

all:	$(HELPFILES) $(HTMLFILES)

.PHONY: clean
clean:
	-rm -f *.qhc *.qch

%.html:	%.txt html.header html.footer
	(cat html.header; markdown2 $<; cat html.footer) > $@

.PHONY: clean
test:
	xmllint --valid --noout $(HTMLFILES)

%.qhc:	%.qhcp lcdoc.qhp $(HTMLFILES)
	qcollectiongenerator $< -o $@

favicon.ico:	favicon32x32.png favicon16x16.png
	png2ico favicon.ico favicon32x32.png favicon16x16.png
