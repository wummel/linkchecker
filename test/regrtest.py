#!/usr/bin/env python

# this file is _not_ the original Python2 regression test suite.

"""Bastis Regression test.

This will find all modules whose name is "test_*" in the test
directory, and run them.  Various command line options provide
additional facilities.

Command line options:

-v, --verbose
        run tests in verbose mode with output to stdout
-q, --quiet
        don't print anything except if a test fails
-g, --generate
        write the output file for a test instead of comparing it
-x, --exclude
        arguments are tests to *exclude*
-r, --random
        randomize test execution order

If non-option arguments are present, they are names for tests to run,
unless -x is given, in which case they are names for tests not to run.
If no test names are given, all tests are run.

-v is incompatible with -g and does not compare test output files.
"""

import sys, getopt, os

sys.path.append(os.getcwd())
from linkcheck import test_support

def main(tests=None, testdir=None, verbose=0, quiet=0, generate=0,
         exclude=0, randomize=0):
    """Execute a test suite.

    This also parses command-line options and modifies its behavior
    accordingly. 

    tests -- a list of strings containing test names (optional)
    testdir -- the directory in which to look for tests (optional)

    Users other than the Python test suite will certainly want to
    specify testdir; if it's omitted, the directory containing the
    Python test suite is searched for.  

    If the tests argument is omitted, the tests listed on the
    command-line will be used.  If that's empty, too, then all *.py
    files beginning with test_ will be used.

    The other seven default arguments (verbose, quiet, generate, exclude,
    single, randomize, and findleaks) allow programmers calling main()
    directly to set the values that would normally be set by flags on the
    command line.

    """
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
	    'vgqxsrl',
	    ['verbose',
	     'generate',
	     'quiet',
	     'exclude',
	     'random',])
    except getopt.error, msg:
        error(msg)
        usage()
        return -1
    for opt, val in opts:
        if opt in ('-v','--verbose'): verbose = verbose + 1
        if opt in ('-q','--quiet'): quiet = 1; verbose = 0
        if opt in ('-g','--generate'): generate = 1
        if opt in ('-x','--exclude'): exclude = 1
        if opt in ('-r','--random'): randomize = 1
    if generate and verbose:
        print "-g and -v don't go together!"
        return 2
    good = []
    bad = []
    skipped = []

    for i in range(len(args)):
        # Strip trailing ".py" from arguments
        if args[i][-3:] == '.py':
            args[i] = args[i][:-3]
    stdtests = STDTESTS[:]
    nottests = NOTTESTS[:]
    if exclude:
        for arg in args:
            if arg in stdtests:
                stdtests.remove(arg)
        nottests[:0] = args
        args = []
    tests = tests or args or findtests(testdir, stdtests, nottests)
    if randomize:
        random.shuffle(tests)
    test_support.verbose = verbose      # Tell tests to be moderately quiet
    save_modules = sys.modules.keys()
    for test in tests:
        if not quiet:
            print test
        ok = runtest(test, generate, verbose, quiet, testdir)
        if ok > 0:
            good.append(test)
        elif ok == 0:
            bad.append(test)
        else:
            skipped.append(test)
        # Unload the newly imported modules (best effort finalization)
        for module in sys.modules.keys():
            if module not in save_modules and module.startswith("test."):
                test_support.unload(module)
    if good and not quiet:
        if not bad and not skipped and len(good) > 1:
            print "All",
        print count(len(good), "test"), "OK."
    if bad:
        print count(len(bad), "test"), "failed:",
        print " ".join(bad)
    if skipped and not quiet:
        print count(len(skipped), "test"), "skipped:",
        print " ".join(skipped)

    return len(bad) > 0

STDTESTS = [
    'test_base',
#    'test_frames',
   ]

NOTTESTS = [
    'test_support',
    ]

def findtests(testdir=None, stdtests=STDTESTS, nottests=NOTTESTS):
    """Return a list of all applicable test modules."""
    if not testdir: testdir = findtestdir()
    names = os.listdir(testdir)
    tests = []
    for name in names:
        if name[:5] == "test_" and name[-3:] == ".py":
            modname = name[:-3]
            if modname not in stdtests and modname not in nottests:
                tests.append(modname)
    tests.sort()
    return stdtests + tests

def runtest(test, generate, verbose, quiet, testdir = None):
    """Run a single test.
    test -- the name of the test
    generate -- if true, generate output, instead of running the test
    and comparing it to a previously created output file
    verbose -- if true, print more messages
    quiet -- if true, don't print 'skipped' messages (probably redundant)
    testdir -- test directory
    """
    test_support.unload(test)
    if not testdir: testdir = findtestdir()
    outputdir = os.path.join(testdir, "output")
    outputfile = os.path.join(outputdir, test)
    try:
        if generate:
            cfp = open(outputfile, "w")
        elif verbose:
            cfp = sys.stdout
        else:
            cfp = Compare(outputfile)
    except IOError:
        cfp = None
        print "Warning: can't open", outputfile
    try:
        save_stdout = sys.stdout
        try:
            if cfp:
                sys.stdout = cfp
                print test              # Output file starts with test name
            __import__(test, globals(), locals(), [])
            if cfp and not (generate or verbose):
                cfp.close()
        finally:
            sys.stdout = save_stdout
    except (ImportError, test_support.TestSkipped), msg:
        if not quiet:
            print "test", test,
            print "skipped -- ", msg
        return -1
    except KeyboardInterrupt:
        raise
    except test_support.TestFailed, msg:
        print "test", test, "failed --", msg
        return 0
    except:
        type, value = sys.exc_info()[:2]
        print "test", test, "crashed --", str(type) + ":", value
        if verbose:
            import traceback
            traceback.print_exc(file=sys.stdout)
        return 0
    else:
        return 1


def findtestdir():
    if __name__ == '__main__':
        file = sys.argv[0]
    else:
        file = __file__
    testdir = os.path.dirname(file) or os.curdir
    return testdir


def count(n, word):
    if n == 1:
        return "%d %s" % (n, word)
    else:
        return "%d %ss" % (n, word)


class Compare:

    def __init__(self, filename):
        self.fp = open(filename, 'r')

    def write(self, data):
        expected = self.fp.read(len(data))
        if data <> expected:
            raise test_support.TestFailed, \
                    'Writing: '+`data`+', expected: '+`expected`

    def writelines(self, listoflines):
        map(self.write, listoflines)

    def flush(self):
        pass

    def close(self):
        leftover = self.fp.read()
        if leftover:
            raise test_support.TestFailed, 'Unread: '+`leftover`
        self.fp.close()

    def isatty(self):
        return 0

if __name__ == '__main__':
    sys.exit(main())
