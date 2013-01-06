ICOICONS := logo16x16.png logo32x32.png
ALLICONS := $(ICOICONS) logo48x48.png logo64x64.png logo128x128.png
OXYGEN := ${HOME}/src/oxygen-gitsvn

all: $(ALLICONS) favicon.ico

logo%.png:	$(OXYGEN)/%/categories/applications-development-web.png
	cp $< $@

favicon.ico:	$(ICOICONS)
	png2ico favicon.ico $(ICOICONS)

