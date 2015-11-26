# This HTML parser needs flex >= 2.5.xx from http://lex.sf.net/ for
# reentrant bison parser support and uses features of bison >= 3.0.x
LEX = flex
YACC = bison
PYINCLUDE=-I/usr/include/python2.7

all: htmllex.c htmlparse.c

htmlsax.so: htmllex.o htmlparse.o s_util.o
	gcc -pthread -shared $^ -o htmlsax.so

%.o:	%.c
	gcc -g -std=c99 -O3 -Wall -pedantic -Wstrict-prototypes -fPIC -I. $(PYINCLUDE) -c $< -o $@

htmlparse.h htmlparse.c:	htmlparse.y htmlsax.h
	$(YACC) --output=htmlparse.c htmlparse.y

htmllex.l:	htmlparse.h

htmllex.c:	htmllex.l htmlsax.h
	$(LEX) htmllex.l
	awk -f fixincludes.awk htmllex.c > htmllex.c.fixed; mv -f htmllex.c.fixed htmllex.c

clean:
	rm -f *.o *.so *.pyc *.pyo *.output

distclean: clean
	rm -f htmlparse.c htmlparse.h htmllex.c

