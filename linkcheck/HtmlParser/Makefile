# this parser needs flex >= 2.5.xx from http://lex.sf.net/
# for reentrant bison parser support!
FLEX = flex
PYVER = 2.4
PYTHON = python$(PYVER)
SPARSE=sparse

all: htmllex.c htmlparse.c

%.o:	%.c
	gcc -g -std=c99 -O3 -Wall -pedantic -Wstrict-prototypes -fPIC -I. -I/usr/include/$(PYTHON) -c $< -o $@

sparse:
	$(SPARSE) -D__STDC__ -I. -I/usr/include/$(PYTHON) -I/usr/lib/gcc/i486-linux-gnu/4.0.3/include s_util.h s_util.c htmlsax.h htmlparse.h htmlparse.c htmllex.c

htmlparse.h htmlparse.c:	htmlparse.y htmlsax.h
	bison htmlparse.y

htmllex.l:	htmlparse.h

htmllex.c:	htmllex.l htmlsax.h
	$(FLEX) htmllex.l
	awk -f fixincludes.awk htmllex.c > htmllex.c.fixed; mv -f htmllex.c.fixed htmllex.c

clean:
	rm -f htmlparse.c htmlparse.h htmllex.c *.o *.so *.pyc *.pyo *.output

splint:
	splint -initallelements +posixlib -I/usr/include/linux -I. -I/usr/include/$(PYTHON) htmllex.c | less
