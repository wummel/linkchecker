# refresh media files

# base directory of oxygen icon set checkout
OXYGEN = $(HOME)/src/oxygen-gitsvn/16x16
#CRYSTAL = $(HOME)/src/crystal_project

ICONS = \
	cancel.png \
	online.png \
	options.png \
	preferences.png \
	start.png \
	stop.png \
	about.png \
	help.png \
	exit.png \
	copy.png

all: $(ICONS)

#app.png:	$(CRYSTAL)/16x16/apps/agt_web.png
#	cp $< $@

start.png:	$(OXYGEN)/actions/media-playback-start.png
	cp $< $@

stop.png:	$(OXYGEN)/actions/media-playback-stop.png
	cp $< $@

cancel.png:	$(OXYGEN)/actions/process-stop.png
	cp $< $@

about.png:	$(OXYGEN)/actions/help-about.png
	cp $< $@

help.png:	$(OXYGEN)/actions/help-contents.png
	cp $< $@

exit.png:	$(OXYGEN)/actions/application-exit.png
	cp $< $@

copy.png:	$(OXYGEN)/actions/edit-copy.png
	cp $< $@

online.png:	$(OXYGEN)/actions/document-open-remote.png
	cp $< $@

options.png:	$(OXYGEN)/categories/preferences-system-network.png
	cp $< $@

preferences.png:	$(OXYGEN)/categories/preferences-other.png
	cp $< $@

clean:
	rm -f *.png
