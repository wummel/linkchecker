#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import sys, os
sys.path.insert(0, os.getcwd())
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
