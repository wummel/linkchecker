po4a:
	po4a --localized-charset=ISO-8859-15 po4a.conf

apidocs:
	epydoc --html -o api --name "LinkChecker source documentation" --url ../index.html ../linkcheck/

clean:
	rm -f *.pyc *.pyo *~

.PHONY: apidocs po4a clean
