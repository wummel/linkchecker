#!/usr/bin/env python

# Written by Martin v. Löwis <loewis@informatik.hu-berlin.de>

"""Generate binary message catalog from textual translation description.

This program converts a textual Uniforum-style message catalog (.po file) into
a binary GNU catalog (.mo file).  This is essentially the same function as the
GNU msgfmt program, however, it is a simpler implementation.

Usage: msgfmt.py [OPTIONS] filename.po

Options:
    -h
    --help
        Print this message and exit.

    -V
    --version
        Display version information and exit.

"""

import sys, getopt, struct, array, string

__version__ = "1.0"
MESSAGES = {}



def usage(code, msg=''):
    sys.stderr.write(__doc__)
    if msg:
        sys.stderr.write(msg)
    sys.exit(code)



def add(id, str, fuzzy):
    "Add a non-fuzzy translation to the dictionary."
    global MESSAGES
    if not fuzzy and str:
        MESSAGES[id] = str



def generate():
    "Return the generated output."
    global MESSAGES
    keys = MESSAGES.keys()
    # the keys are sorted in the .mo file
    keys.sort()
    offsets = []
    ids = strs = ''
    for id in keys:
        # For each string, we need size and file offset.  Each string is NUL
        # terminated; the NUL does not count into the size.
        offsets.append((len(ids), len(id), len(strs), len(MESSAGES[id])))
        ids = ids + id + '\0'
        strs = strs + MESSAGES[id] + '\0'
    output = ''
    # The header is 7 32-bit unsigned integers.  We don't use hash tables, so
    # the keys start right after the index tables.
    # translated string.
    keystart = 7*4+16*len(keys)
    # and the values start after the keys
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    # The string table first has the list of keys, then the list of values.
    # Each entry has first the size of the string, then the file offset.
    for o1, l1, o2, l2 in offsets:
        koffsets = koffsets + [l1, o1+keystart]
        voffsets = voffsets + [l2, o2+valuestart]
    offsets = koffsets + voffsets
    output = struct.pack("iiiiiii",
                         0x950412de,        # Magic
                         0,                 # Version
                         len(keys),         # # of entries
                         7*4,               # start of key index
                         7*4+len(keys)*8,   # start of value index
                         0, 0)              # size and offset of hash table
    output = output + array.array("i", offsets).tostring()
    output = output + ids
    output = output + strs
    return output



def make(filename):
    ID = 1
    STR = 2

    # Compute .mo name from .po name
    if filename[-3:] == '.po':
        infile = filename
        outfile = filename[:-2] + 'mo'
    else:
        infile = filename + '.po'
        outfile = filename + '.mo'
    try:
        lines = open(infile).readlines()
    except IOError, msg:
        sys.stderr.write(msg)
        sys.exit(1)
    
    section = None
    fuzzy = 0

    # Parse the catalog
    lno = 0
    for l in lines:
        lno = lno + 1
        # If we get a comment line after a msgstr, this is a new entry
        if l[0] == '#' and section == STR:
            add(msgid, msgstr, fuzzy)
            section = None
            fuzzy = 0
        # Record a fuzzy mark
        if l[:2] == '#,' and string.find(l, 'fuzzy') != -1:
            fuzzy = 1
        # Skip comments
        if l[0] == '#':
            continue
        # Now we are in a msgid section, output previous section
        if l[:5] == 'msgid':
            if section == STR:
                add(msgid, msgstr, fuzzy)
            section = ID
            l = l[5:]
            msgid = msgstr = ''
        # Now we are in a msgstr section
        elif l[:6] == 'msgstr':
            section = STR
            l = l[6:]
        # Skip empty lines
        l = string.strip(l)
        if not l:
            continue
        # XXX: Does this always follow Python escape semantics?
        l = eval(l)
        if section == ID:
            msgid = msgid + l
        elif section == STR:
            msgstr = msgstr + l
        else:
            sys.stderr.write('Syntax error on %s:%d\n'
	                     'before: %s\n' % (infile, lno, l))
            sys.exit(1)
    # Add last entry
    if section == STR:
        add(msgid, msgstr, fuzzy)

    # Compute output
    output = generate()

    # Save output
    try:
        open(outfile,"wb").write(output)
    except IOError,msg:
        sys.stderr.write(msg)
                      


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hV', ['help','version'])
    except getopt.error, msg:
        usage(1, msg)

    # parse options
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-V', '--version'):
            sys.stderr.write("msgfmt.py %s" % __version__)
            sys.exit(0)
    # do it
    if not args:
        sys.stderr.write('No input file given\n')
        sys.stderr.write("Try `msgfmt --help' for more information.\n")
        return

    for filename in args:
        make(filename)


if __name__ == '__main__':
    main()
