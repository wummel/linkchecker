# generate Python files from UI description

# edit ui/*.ui files with designer (ie. /usr/bin/designer-qt4)
UI_FILES = linkchecker_ui_main.py \
	linkchecker_ui_options.py \
	linkchecker_ui_debug.py \
	linkchecker_ui_editor.py
RC_FILES = linkchecker_rc.py


all: $(UI_FILES) $(RC_FILES)

linkchecker_ui_%.py: ui/%.ui
	pyuic4 -o $@ $<
# replace the Qt translator with the one LinkChecker uses
	sed -i -r -e 's/QtGui\.QApplication\.translate\("[^"]+", "([^"]+)", None, QtGui\.QApplication\.UnicodeUTF8\)/_("\1")/g' $@

linkchecker_rc.py: rc/linkchecker.qrc
	pyrcc4 -o $@ $<

clean:
	rm -f *.pyc *.pyo

rebuild:
	rm -f $(UI_FILES) $(RC_FILES)
	$(MAKE) all
