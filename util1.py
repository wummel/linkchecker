"""
    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
import sys,time,rotor,types

_curses = None
try:
    from ncurses import curses
    _curses = curses
except ImportError:
    try:
        import curses
        _curses = curses
    except ImportError:
        pass

_bs = [
['\023\335\233\203\2323\016',
 '\023\335\233\215\324\244\016',
 '\023\335v\215.\244\377K',
 '\023\245\304\304.\205\027\2730',
 '\023\335\377{\232\207\372K'],
['\023\335\233q\005\016\016',
 '\023\335\233\215\324\244\016',
 '\023\335v\215.\244\377K',
 '\023\245\304\304.\205\027\2730',
 '\023\335\377{\232\207\372K'],
['\023\335\233J\232\233\016',
 '\023\335\233\215\324\244\016',
 '\023\335v\215.\244\377K',
 '\023\245\304\304.\205\027\2730',
 '\023\335\377{\232\207\372K']]


_ss = [
['\023\335\340\275\247\205',
 '\023\335v\347\216\205',
 '\023\245\304\304\363\244\016',
 '\023\303\377J\005\354\016'],
['\023\335\340\275\247\205',
 '\023\335v\370\216\205',
 '\023\245\304\304\363\244\016',
 '\023\303\377J\005\354\016'],
['\023\335\340\305\330\205',
 '\023\335v\347\216\205',
 '\023\245\304\304\363\244\016',
 '\023\303\377J\005\354\016']]

_1 = '\001\347k\304}\203\265(Y\261\357\220\240lL\026\377\234lz\362w\372\015)\366\232p\267\220nL\3238%\343\310\362\037\331\022\355r\334\237$\203w\037C:^\240_\2351\217'
_2 = '\035\177\271uC\203\016\306h\2016OHT\352Gw\3770\202fl\013S\021\016\370'
_3 = '\236\177\246\304\351F\203(\005z\375\220\324)\201\266z*j\342\344l\323\0325\374:Z\313\212hD\256\334?a\034\274\315\004r\012a\334\237$\203w\037'
_4 = '\222\360P\277\330\300\246\3670\256\303\223\036\311['

def abbuzze():
    if not _curses:
        print "Sorry, this operating system can not wash clothes."
        return
    w = _curses.initscr() # initialize the curses library
    config_curses()
    my,mx = w.getmaxyx()
    b = w.subwin(my-2, mx, 0, 0)
    s = w.subwin(2, mx, my-2, 0)
    if color:
        s.color_set(1)
    bs = nassmache(_bs)
    ss = nassmache(_ss)
    allahopp(s, nassmache(_1))
    tadaaa(b, ss[0])
    allahopp(s, nassmache(_2))
    wischi(b, ss)
    allahopp(s, nassmache(_3))
    tadaaa(b, bs[0])
    waschi(b, bs)
    allahopp(s, nassmache(_4))
    abspann(curses.newwin(8, 30, 0, 0))
    w.erase()
    w.refresh()
    _curses.endwin()

def config_curses():
    _curses.nonl()            # tell curses not to do NL->CR/NL on output
    _curses.noecho()          # don't echo input
    _curses.cbreak()          # take input chars one at a time, no wait for \n
    global color
    if hasattr(_curses, "start_color"):
        color = 1
        _curses.start_color() # start the colour system
        if _curses.has_colors():
            if _curses.can_change_color():
                pass
            else:
                _curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                _curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                _curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                _curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    else:
        color = 0

def waddemol(f):
    time.sleep(float(f))

def nassmache(henne):
    if type(henne) == types.StringType:
        return rotor.newrotor('ramdoesiger Malaker').decrypt(henne)
    hase = []
    for ei in henne:
        hase.append(nassmache(ei))
    return hase

def allahopp(w, s, y=2):
    w.erase()
    w.move(0,y)
    for i in range(len(s)):
        w.addch(ord(s[i]))
        waddemol(0.14)
        w.refresh()
    waddemol(0.7)

def tadaaa(w, l):
    w.erase()
    my,mx = w.getmaxyx()
    for p in range(mx/2):
        hotzenplotz(w, my/3, p, l)
        w.refresh()
        waddemol(0.15)

def hotzenplotz(w,y,x,l):
    for li in l:
        w.move(y,x)
        w.addstr(li)
        y = y+1

def wischi(w, ls):
    my,mx = w.getmaxyx()
    f = 0.2
    i=0
    j=0
    up = 1
    w.erase()
    while i<11:
        i = i+1
        j = j + (up and 1 or -1)
        if j==-1: up = 1
        elif j==1: up = 0
        hotzenplotz(w,my/3,mx/2+j,ls[j+1])
        w.refresh()
        waddemol(f)

def waschi(w, l):
    wischi(w,l)

def abspann(w):
    w.erase()
    w.border(0, 0, 0, 0, 0, 0, 0, 0)
    w.refresh()
    w1 = w.subwin(1, 20, 3, 4)
    w2 = w.subwin(1, 20, 5, 4)
    allahopp(w1, "Tux wishy washy", 0)
    allahopp(w1, "Author:", 0)
    allahopp(w2, "Bastian Kleineidam", 0)
    allahopp(w1, "Featuring:", 0)
    allahopp(w2, "Little Tux", 0)
    allahopp(w2, "Big Tux", 0)
    waddemol(1)

if __name__=='__main__':
    try:
        abbuzze()
    except:
        _curses.endwin()
        type, value = sys.exc_info()[:2]
        print type,value
        print "Sorry, your washing machine is broken!"
