#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2009 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
A script to lossless compress media files to be used in production
deployments of web software. Used together with HTML compression
it decreases the size of transmitted data considerably.

Currently supported media files:
  Type       Extension  Compressor(s)
========================================================
JavaScript  .js         YUI compressor (a Java program)
CSS         .css        YUI compressor (a Java program)
PNG         .png        pngcrush (a C program)
JPEG        .jpg        jpegtran (a C program)
GIF         .gif        giftrans (a C program)

It compresses all supported media files to new files. The original
files will not be changed if not explicitely requested.

Compressed files will be named <filebase>-min.<ext> where <filebase> is
everything up to the last dot and <ext> is everything after the last dot.
If requested, the original file will be overwritten with the compressed one.

A directory will be recursively searched and all media files within will
be compressed.

Files will only be compressed when the compressed file is missing or the
original file is newer than the compressed file.
"""
import sys
import os
import getopt
import stat
import shutil
from distutils.spawn import spawn, find_executable
from distutils.errors import DistutilsExecError
import distutils.log
distutils.log.set_verbosity(1)


# list of extensions for compressable files
COMPRESS_EXTENSIONS = (".js", ".css", ".png", ".jpg", ".gif")


def log (*args):
    for arg in args:
        print >> sys.stderr, arg,
    print >> sys.stderr


def usage (msg=None):
    """
    Print usage information to sys.stderr and call sys.exit().
    The exit code is zero if msg is None, else one.
    """
    if msg is None:
        err = 0
    else:
        print >> sys.stderr, msg
        err = 1
    thisfile = os.path.basename(__file__)
    log("Usage:", thisfile, "[options]", "<file-or-directory>...")
    log("Options:")
    log("  --js-compressor - Specify the JavaScript compressor " \
        "(default: yuicompressor.jar)")
    log("  --exclude - Specify (part of) filenames to ignore")
    log("  --overwrite - Comma-separated list of file extensions to overwrite")
    log("  --help - Display help")
    sys.exit(err)


class DirectoryWalker:

    def __init__(self, directory):
        self.stack = [directory]
        self.files = []
        self.index = 0

    def __getitem__(self, index):
        while 1:
            try:
                file = self.files[self.index]
                self.index = self.index + 1
            except IndexError:
                # pop next directory from stack
                self.directory = self.stack.pop()
                self.files = os.listdir(self.directory)
                self.index = 0
            else:
                # got a filename
                fullname = os.path.join(self.directory, file)
                if os.path.isdir(fullname) and not os.path.islink(fullname):
                    self.stack.append(fullname)
                return fullname


def is_compressable (settings, filename):
    "Check if given filename is compressable."
    # is it excluded?
    if [x for x in settings["exclude"] if x in filename]:
        return False
    # is it compressable?
    return os.path.splitext(filename)[1] in COMPRESS_EXTENSIONS


def get_files (settings, args):
    """
    Given a list of files and/or directories return all compressable
    files as an iterator.
    """
    for arg in args:
        if os.path.isdir(arg):
            for file in DirectoryWalker(arg):
                if is_compressable(settings, file):
                    yield file
        elif os.path.isfile(arg):
            if is_compressable(settings, arg):
                yield arg
        else:
            log("Warning: not a file or directory", repr(arg))


settings = {
    # default compress executables
    "compressor": {
        ".js": "yuicompressor.jar", # Note: automatically suffixes with "java"
        ".css": "yuicompressor.jar",
        ".png": "pngcrush",
        ".jpg": "jpegtran",
        ".gif": "giftrans",
    },
    # list of filenames (or a part of them) to exclude
    "exclude": set(),
    # list of file extensions to overwrite
    "overwrite": set(),
}
def parse_options (args):
    """
    Parse command line arguments.
    @return: (settings, args)
    @rtype: tuple (dict, list)
    """
    long_opts = ["help", "js-compressor=", "exclude=", "overwrite="]
    try:
        opts, args = getopt.getopt(args, "", long_opts)
    except getopt.error:
        usage(msg=sys.exc_info()[1])
    for opt, arg in opts:
        if opt == "--help":
            usage()
        elif opt == "--js-compressor":
            for ext in (".js", ".css"):
                settings["compressor"][ext] = arg
        elif opt == "--exclude":
            settings["exclude"].add(arg)
        elif opt == "--overwrite":
            exts = [x.strip().lower() for x in arg.split(",") if x]
            settings["overwrite"].update(exts)
        else:
            usage(msg="Unbekannte Option %r" % opt)
    return settings, args


def get_mtime (filename):
    "Return modification time of file."
    return os.stat(filename)[stat.ST_MTIME]


def get_fsize (filename):
    "Return file size in bytes."
    return os.stat(filename)[stat.ST_SIZE]


def needs_compression (infile, outfile):
    "Check if infile needs to be compressed to given outfile."
    if not os.path.exists(outfile):
        return True
    return get_mtime(infile) > get_mtime(outfile)


def compress_file (infile):
    "Compress given file if needed."
    base, ext = os.path.splitext(infile)
    if base.endswith("-min"):
        #log("Ignoring", repr(infile))
        return
    outfile = "%s-min%s" % (base, ext)
    if needs_compression(infile, outfile):
        cmd = compress_cmd(ext, infile, outfile)
        if not cmd:
            log("Skipping", repr(infile), "no compressor available")
            return
        try:
            log("Compressing", repr(infile), "...")
            run_cmd(cmd)
        except DistutilsExecError, msg:
            log("Error running %s: %s" % (cmd, msg))
        else:
            insize = get_fsize(infile)
            outsize = get_fsize(outfile)
            if outsize > insize:
                log("Warning: compressed file is bigger than original "
                    "(%dB > %dB); copying instead." % (insize, outsize))
                shutil.copyfile(infile, outfile)
            else:
                percentage = float(outsize * 100) / insize
                log(".. compressed to %.2f%% (%dB -> %dB)" % \
                    (percentage, insize, outsize))
            if ext[1:].lower() in settings["overwrite"]:
                shutil.move(outfile, infile)
    else:
        log("Skipping", repr(infile))


def compress_cmd (ext, infile, outfile):
    "Get list of commands args for compression."
    cmd = []
    compressor = settings["compressor"][ext]
    if compressor.endswith(".jar"):
        if not find_executable("java"):
            return None
        cmd.insert(0, "java")
        cmd.insert(1, "-jar")
    elif not find_executable(compressor):
        return None
    cmd.append(compressor)
    cmd.extend(compressor_args(compressor, infile, outfile))
    return cmd


def compressor_args (compressor, infile, outfile):
    """
    Return list of commandline arguments that compress infile to outfile
    with given compressor.
    """
    basename = os.path.basename(compressor).lower()
    if basename.startswith("yuicompressor"):
        args = compressor_args_yui(infile, outfile)
    elif basename.startswith("pngcrush"):
        args = compressor_args_pngcursh(infile, outfile)
    elif basename.startswith("jpegtran"):
        args = compressor_args_jpegtran(infile, outfile)
    elif basename.startswith("giftrans"):
        args = compressor_args_giftrans(infile, outfile)
    else:
        raise getopt.error("Unknown compressor %r" % compressor)
    return args


def compressor_args_yui (infile, outfile):
    return ["--charset", "utf8", "-o", outfile, infile]

def compressor_args_pngcursh (infile, outfile):
    return [infile, outfile]

def compressor_args_jpegtran (infile, outfile):
    return ["-optimize", "-perfect", "-copy", "none",
            "-outfile", outfile, infile]

def compressor_args_giftrans (infile, outfile):
    return ["-C", "-o", outfile, infile]


def run_cmd (cmd):
    "Execute given command."
    return spawn(cmd)


def main (args):
    settings, args = parse_options(args)
    for file in get_files(settings, args):
        compress_file(file)


if __name__ == '__main__':
    main(sys.argv[1:])
