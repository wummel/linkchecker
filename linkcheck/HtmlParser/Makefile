# this parser needs flex >= 2.5.xx from http://lex.sf.net/
# for reentrant bison parser support
FLEX = flex
PYINCLUDE=-I/usr/include/python2.7
#PYINCLUDE="-I/home/calvin/src/python-gitsvn -I/home/calvin/src/python-gitsvn/Include"

all: htmllex.c htmlparse.c

htmlsax.so: htmllex.o htmlparse.o s_util.o
	gcc -pthread -shared $^ -o htmlsax.so

%.o:	%.c
	gcc -g -std=c99 -O3 -Wall -pedantic -Wstrict-prototypes -fPIC -I. $(PYINCLUDE) -c $< -o $@

htmlparse.h htmlparse.c:	htmlparse.y htmlsax.h
	bison htmlparse.y

htmllex.l:	htmlparse.h

htmllex.c:	htmllex.l htmlsax.h
	$(FLEX) htmllex.l
	awk -f fixincludes.awk htmllex.c > htmllex.c.fixed; mv -f htmllex.c.fixed htmllex.c

clean:
	rm -f *.o *.so *.pyc *.pyo *.output

distclean: clean
	rm -f htmlparse.c htmlparse.h htmllex.c

