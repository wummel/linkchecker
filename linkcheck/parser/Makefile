# parser needs flex >= 2.5.xx from http://lex.sf.net/
# for reentrant bison parser support!
FLEX=flex
PYVER=2.3
PYTHON=python$(PYVER)

all: htmllex.c htmlparse.c

%.o:	%.c
	gcc -g -O3 -Wall -pedantic -Wstrict-prototypes -fPIC -I. -I/usr/include/$(PYTHON) -c $< -o $@

htmlparse.h htmlparse.c:	htmlparse.y htmlsax.h
	bison htmlparse.y

htmllex.l:	htmlparse.h

htmllex.c:	htmllex.l htmlsax.h
	$(FLEX) htmllex.l

test:	testsax
	cat test.html | ./testsax

clean:
	rm -f htmlparse.c htmlparse.h htmllex.c *.o *.output

splint:
	splint -initallelements +posixlib -I/usr/include/linux -I. -I/usr/include/$(PYTHON) htmllex.c | less
