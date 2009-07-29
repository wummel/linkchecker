HELPFILES = lccollection.qhc

all:	$(HELPFILES)

.PHONY: clean
clean:
	-rm -f *.qhc *.qch

%.qhc:	%.qhcp lcdoc.qhp
	qcollectiongenerator $< -o $@

favicon.ico:	favicon32x32.png favicon16x16.png
	png2ico favicon.ico favicon32x32.png favicon16x16.png
