#!/usr/bin/env python
import sys
sys.path.insert(0, ".")
from linkcheck.parser.htmllib import HtmlPrinter

def _main():
    #pass
    file = sys.argv[1]
    data = open(file).read()
    p = HtmlPrinter()
    p.feed(data)
    p.flush()

if __name__=='__main__':
    _main()
