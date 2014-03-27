#!/usr/bin/env python
"""
View yappi profiling data.

Usage: $0 <filename>
"""
import sys
import yappi

def main(args):
    filename = args[0]
    stats = yappi.YFuncStats()
    stats.add(filename)
    stats.print_all()


if __name__ == '__main__':
   main(sys.argv[1:])

