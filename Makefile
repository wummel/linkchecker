# This Makefile is only used by developers.
# You will need a Debian Linux system to use this Makefile because
# some targets produce Debian .deb packages
VERSION=$(shell python setup.py --version)
PACKAGE = linkchecker
NAME = $(shell python setup.py --name)
HOST=treasure.calvinsplayground.de
#LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
LCOPTS=-ocolored -Ftext -Fhtml -Fgml -Fsql -Fcsv -Fxml -R -t0 -v -s
DEBPACKAGE = $(PACKAGE)_$(VERSION)_i386.deb
PULLHOST=phoenix.net.uni-sb.de
PULLPATH=/home/calvin/temp/linkchecker

DESTDIR=/.
.PHONY: test clean distclean package files upload dist locale all

all:
	@echo "Read the file INSTALL to see how to build and install"

clean:
	-python setup.py clean --all # ignore errors of this command
	$(MAKE) -C po clean
	find . -name '*.py[co]' | xargs rm -f

distclean: clean cleandeb
	rm -rf dist build # just to be sure clean also the build dir
	rm -f $(PACKAGE)-out.* VERSION LinkCheckerConf.py MANIFEST Packages.gz

cleandeb:
	rm -rf debian/$(PACKAGE) debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

dist:	locale
	fakeroot debian/rules binary
	# cleandeb because distutils choke on dangling symlinks
	# (linkchecker.1 -> undocumented.1)
	$(MAKE) cleandeb
	python setup.py sdist --formats=gztar,zip bdist_rpm
	# extra run without SSL compilation
	python setup.py bdist_wininst
	mv -f ../$(DEBPACKAGE) dist

package:
	cd dist && dpkg-scanpackages . ../override.txt | gzip --best > Packages.gz

files:	locale
	./$(PACKAGE) $(LCOPTS) -i$(HOST) http://$(HOST)/~calvin/

VERSION:
	echo $(VERSION) > VERSION

upload: distclean dist package files VERSION
	scp debian/changelog shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/changes.txt
	scp README shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/readme.txt
	scp linkchecker-out.* shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs
	scp VERSION shell1.sourceforge.net:/home/groups/$(PACKAGE)/htdocs/raw/
	scp dist/* shell1.sourceforge.net:/home/groups/ftp/pub/$(PACKAGE)/
	ssh -C -t shell1.sourceforge.net "cd /home/groups/$(PACKAGE) && make"

uploadpull: distclean dist package files VERSION
	# shit, need to make pull, scp upload is not working any more
	# aha, sourceforge fixed the shells, use upload again :)
	ssh -t $(PULLHOST) "cd $(PULLPATH) && make clean"
	scp debian/changelog README linkchecker-out.* VERSION $(PULLHOST):$(PULLPATH)
	scp dist/* $(PULLHOST):$(PULLPATH)/dist
	ssh -C -t shell1.sourceforge.net "cd /home/groups/$(PACKAGE) && make pull"

test:
	rm -f test/*.result
	@for i in test/*.html; do \
	  echo "Testing $$i. Results are in $$i.result"; \
	  ./$(PACKAGE) -r1 -ucalvin -pcalvin -otext -N"news.rz.uni-sb.de" -v -a $$i > $$i.result 2>&1; \
        done

locale:
	$(MAKE) -C po
