HOMEPAGE:=$(HOME)/public_html/linkchecker-webpage.git
WOK:=$(HOME)/projects/wok.git/wok
ICOICONS := media/images/logo16x16.png media/images/logo32x32.png
ALLICONS := $(ICOICONS) media/images/logo48x48.png media/images/logo64x64.png media/images/logo128x128.png
OXYGEN := $(HOME)/src/oxygen-gitsvn

all:

logo%.png:	$(OXYGEN)/%/categories/applications-development-web.png
	cp $< $@

media/favicon.ico:	$(ICOICONS)
	png2ico $@ $(ICOICONS)

gen:	$(ALLICONS) media/favicon.ico
	$(WOK) -v --debug

serve:
	xdg-open http://localhost:8080
	$(WOK) --server localhost:8080

upload:
	cd $(HOMEPAGE) && git add . && git commit -m "Updated" && git push

release: gen upload

.PHONY: all gen serve upload release
