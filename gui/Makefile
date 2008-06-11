# generate Python files from UI description

UI_FILES = linkchecker_ui.py

all: $(UI_FILES)

linkchecker_ui.py: ui/mainwindow.ui
	pyuic4 -tr _ -o $@ $<

#linkchecker_rc.py: linkchecker.qrc
#	pyrcc4 -o $@ $<

run:
	env PYTHONPATH=.:.. python linkchecker-gui
