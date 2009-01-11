# refresh media files

# base directory of oxygen icon set checkout
OXYGEN = /home/calvin/src/oxygen-gitsvn/16x16

ICONS = \
	cancel.png \
	options.png \
	preferences.png \
	start.png \
	stop.png \

all: $(ICONS)

start.png:	$(OXYGEN)/actions/media-playback-start.png
	cp $< $@

stop.png:	$(OXYGEN)/actions/media-playback-stop.png
	cp $< $@

cancel.png:	$(OXYGEN)/actions/process-stop.png
	cp $< $@

options.png:	$(OXYGEN)/categories/preferences-system-network.png
	cp $< $@

preferences.png:	$(OXYGEN)/categories/preferences-other.png
	cp $< $@

clean:
	rm -f *.png
