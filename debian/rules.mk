configure: configure-stamp
configure-stamp:
	dh_testdir
	./setup.py config -lcrypto
	touch configure-stamp


build: configure-stamp build-stamp
build-stamp:
	dh_testdir
	rm -rf debian/linkchecker debian/linkchecker-ssl
	./setup.py build
	touch build-stamp

clean:
	dh_testdir
	rm -f build-stamp configure-stamp
	$(MAKE) clean
	dh_clean

