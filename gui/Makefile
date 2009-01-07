# generate Python files from UI description

# edit ui/*.ui files with designer
UI_FILES = linkchecker_ui_main.py linkchecker_ui_options.py
RC_FILES = linkchecker_rc.py


all: $(UI_FILES) $(RC_FILES)

linkchecker_ui_%.py: ui/%.ui
	pyuic4 -o $@ $<

linkchecker_rc.py: rc/linkchecker.qrc
	pyrcc4 -o $@ $<

run:
	env PYTHONPATH=.:.. python linkchecker-gui

clean:
	rm -f *.pyc *.pyo
