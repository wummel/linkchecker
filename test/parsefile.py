#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import sys
from linkcheck.parser.htmllib import HtmlPrinter

def _main (filename):
    data = file(filename).read()
    p = HtmlPrinter()
    p.feed(data)
    p.flush()

if __name__=='__main__':
    _main(sys.argv[1])
