HELPFILES = lccollection.qhc

all:	$(HELPFILES)

clean:
	-rm -f *.qhc *.qch

test:
	xmllint --valid --noout *.html


%.qhc:	%.qhcp lcdoc.qhp
	qcollectiongenerator $< -o $@

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

api:
	epydoc --html -o api --name "LinkChecker source documentation" --url ../index.html ../linkcheck/

.PHONY: po4a api clean
favicon.ico:	favicon32x32.png favicon16x16.png
	png2ico favicon.ico favicon32x32.png favicon16x16.png

