HELPFILES = lccollection.qhc

all:	$(HELPFILES) index.html

.PHONY: clean
clean:
	-rm -f *.qhc *.qch

%.html:	%.txt html.header html.footer
	(cat html.header; markdown2 $<; cat html.footer) > index.html

%.qhc:	%.qhcp lcdoc.qhp index.html
	qcollectiongenerator $< -o $@

favicon.ico:	favicon32x32.png favicon16x16.png
	png2ico favicon.ico favicon32x32.png favicon16x16.png
