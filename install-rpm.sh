python2.4 setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
# 'brp-compress' compresses the manpages without distutils knowing.
# The sed scripts append ".gz" resp. ".bz2" suffixes to the affected
# manpage filenames.
if [ -n "$( ls $RPM_BUILD_ROOT/usr/share/man/man*/*.bz2 2>/dev/null )" ]; then
    sed -i -e 's@man/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/man\1/\2.bz2@g' INSTALLED_FILES
    sed -i -e 's@man/de/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/de/man\1/\2.bz2@g' INSTALLED_FILES
    sed -i -e 's@man/fr/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/fr/man\1/\2.bz2@g' INSTALLED_FILES
else
    sed -i -e 's@man/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/man\1/\2.gz@g' INSTALLED_FILES
    sed -i -e 's@man/de/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/de/man\1/\2.gz@g' INSTALLED_FILES
    sed -i -e 's@man/fr/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/fr/man\1/\2.gz@g' INSTALLED_FILES
fi
