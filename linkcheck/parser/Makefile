# use beta flex from ftp://ftp.uncg.edu/people/wlestes/ for reentrant
# bison parser support
FLEX=/home/calvin/src/flex-2.5.25/flex

all: htmllex.c htmlparse.c

%.o:	%.c
	gcc -g -O -Wall -pedantic -Wstrict-prototypes -fPIC -I. -I/usr/include/python2.1 -c $< -o $@

htmlparse.h htmlparse.c:	htmlparse.y htmlsax.h
	bison htmlparse.y

htmllex.l:	htmlparse.h

htmllex.c:	htmllex.l htmlsax.h
	$(FLEX) htmllex.l

test:	testsax
	cat test.html | ./testsax

clean:
	rm -f htmlparse.c htmlparse.h htmllex.c *.o *.output
