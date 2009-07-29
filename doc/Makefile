all:

test:
	xmllint --valid --noout *.html

po4a:
	po4a --localized-charset=UTF-8 po4a.conf

api:
	epydoc --html -o api --name "LinkChecker source documentation" --url ../index.html ../linkcheck/

.PHONY: po4a api test
