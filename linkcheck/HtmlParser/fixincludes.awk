# Add htmlsax.h include as first line of file. This is needed to let
# Python.h be included before any system headers.
# See also http://docs.python.org/api/includes.html
BEGIN {
    print "#include \"htmlsax.h\"";
}
{ print; }
