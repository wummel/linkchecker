python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
# 'brp-compress' gzips the man pages without distutils knowing... fix this
sed -i -e 's@man/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)\.gz$@man/man\1/\2@g' INSTALLED_FILES
