#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2003 Shuttleworth Foundation
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
SchoolTool test runner.

Syntax: test.py [options] [pathname-regexp [test-regexp]]

Test cases are located in the directory tree starting at the location of this
script, in subdirectories named 'tests' and in Python modules named
'test*.py'. They are then filtered according to pathname and test regexes.
Alternatively, packages may just have 'tests.py' instead of a subpackage
'tests'.

A leading "!" in a regexp is stripped and negates the regexp.  Pathname
regexp is applied to the whole path (package/package/module.py). Test regexp
is applied to a full test id (package.package.module.class.test_method).

Options:
  -h, --help            print this help message
  -v                    verbose (print dots for each test run)
  -vv                   very verbose (print test names)
  -q                    quiet (do not print anything on success)
  -c                    colorize output
  -d                    invoke pdb when an exception occurs
  -1                    report only the first failure in doctests
  -p                    show progress bar (can be combined with -v or -vv)
  --level n             select only tests at level n or lower
  --all-levels          select all tests
  --list-files          list all selected test files
  --list-tests          list all selected test cases
  --coverage            create code coverage reports
  --profile             profile the unit tests
  --search-in dir       limit directory tree walk to dir (optimisation)
  --immediate-errors    show errors as soon as they happen (default)
  --delayed-errors      show errors after all tests were run
  --resource name       enable given resource
"""
#
# This script borrows ideas from Zope 3's test runner heavily.  It is smaller
# and cleaner though, at the expense of more limited functionality.
#

import re
import os
import sys
import time
import types
import getopt
import unittest
import traceback
import linecache
import pdb

__metaclass__ = type

RCS_IGNORE = [
    "SCCS",
    "BitKeeper",
    "CVS",
    ".pc",
    ".hg",
    ".svn",
    ".git",
]


class Options:
    """Configurable properties of the test runner."""

    # test location
    basedir = 'src'                # base directory for tests (defaults to
                                # basedir of argv[0]), must be absolute
    search_in = ()              # list of subdirs to traverse (defaults to
                                # basedir)
    follow_symlinks = True      # should symlinks to subdirectories be
                                # followed? (hardcoded, may cause loops)
    # available resources
    resources = []

    # test filtering
    level = 1                   # run only tests at this or lower level
                                # (if None, runs all tests)
    pathname_regex = ''         # regexp for filtering filenames
    test_regex = ''             # regexp for filtering test cases

    # actions to take
    list_files = False          # --list-files
    list_tests = False          # --list-tests
    run_tests = True            # run tests (disabled by --list-foo)
    postmortem = False          # invoke pdb when an exception occurs
    profile = False

    # output verbosity
    verbosity = 0               # verbosity level (-v)
    quiet = 0                   # do not print anything on success (-q)
    first_doctest_failure = False # report first doctest failure (-1)
    print_import_time = True    # print time taken to import test modules
                                # (currently hardcoded)
    progress = False            # show running progress (-p)
    colorize = False            # colorize output (-c)
    coverage = False            # produce coverage reports (--coverage)
    coverdir = 'coverage'       # where to put them (currently hardcoded)
    immediate_errors = True     # show tracebacks twice (--immediate-errors,
                                # --delayed-errors)
    screen_width = 80           # screen width (autodetected)


def compile_matcher(regex):
    """Return a function that takes one argument and returns True or False.

    Regex is a regular expression.  Empty regex matches everything.  There
    is one expression: if the regex starts with "!", the meaning of it is
    reversed.
    """
    if not regex:
        return lambda x: True
    elif regex == '!':
        return lambda x: False
    elif regex.startswith('!'):
        rx = re.compile(regex[1:])
        return lambda x: rx.search(x) is None
    else:
        rx = re.compile(regex)
        return lambda x: rx.search(x) is not None


def walk_with_symlinks(top, func, arg):
    """Like os.path.walk, but follows symlinks on POSIX systems.

    If the symlinks create a loop, this function will never finish.
    """
    try:
        names = os.listdir(top)
    except os.error:
        return
    func(arg, top, names)
    exceptions = ('.', '..')
    for name in names:
        if name not in exceptions:
            name = os.path.join(top, name)
            if os.path.isdir(name):
                walk_with_symlinks(name, func, arg)


def has_path_component (path, name):
    drive, path = os.path.splitdrive(path)
    head, tail = os.path.split(path)
    while head and tail:
        if tail == name:
            return True
        head, tail = os.path.split(head)
    return False


def get_test_files(cfg):
    """Return a list of test module filenames."""
    matcher = compile_matcher(cfg.pathname_regex)
    allresults = []
    test_names = ['tests']
    baselen = len(cfg.basedir) + 1
    def visit(ignored, dir, files):
        # Ignore files starting with a dot.
        # Do not not descend into subdirs containing a dot.
        # Ignore versioning system files
        remove = []
        for idx, file in enumerate(files):
            if file.startswith('.'):
                remove.append(idx)
            elif '.' in file and os.path.isdir(os.path.join(dir, file)):
                remove.append(idx)
            elif file in RCS_IGNORE:
                remove.append(idx)
        remove.reverse()
        for idx in remove:
            del files[idx]
        # Skip non-test directories, but look for tests.py
        if not has_path_component(dir, test_name):
            if test_name + '.py' in files:
                path = os.path.join(dir, test_name + '.py')
                if matcher(path[baselen:]):
                    results.append(path)
            return
        test_files = [f for f in files if \
                      f.startswith('test') and f.endswith(".py")]
        if '__init__.py' not in files:
            if test_files:
                # Python test files found, but no __init__.py
                print >> sys.stderr, "%s is not a package" % dir
            return
        for file in test_files:
            path = os.path.join(dir, file)
            if matcher(path[baselen:]):
                results.append(path)
    if cfg.follow_symlinks:
        walker = walk_with_symlinks
    else:
        walker = os.path.walk

    for test_name in test_names:
        results = []
        for dir in cfg.search_in:
            walker(dir, visit, None)
        results.sort()
        allresults += results

    return allresults


def import_module(filename, cfg, tracer=None):
    """Import and return a module."""
    filename = os.path.splitext(filename)[0]
    modname = filename[len(cfg.basedir):].replace(os.path.sep, '.')
    if modname.startswith('.'):
        modname = modname[1:]
    if tracer is not None:
        mod = tracer.runfunc(__import__, modname)
    else:
        mod = __import__(modname)
    components = modname.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def filter_testsuite(suite, matcher, level=None):
    """Return a flattened list of test cases that match the given matcher."""
    if not isinstance(suite, unittest.TestSuite):
        raise TypeError('not a TestSuite', suite)
    results = []
    for test in suite._tests:
        if level is not None and getattr(test, 'level', 0) > level:
            continue
        if isinstance(test, unittest.TestCase):
            testname = test.id() # package.module.class.method
            if matcher(testname):
                results.append(test)
        else:
            filtered = filter_testsuite(test, matcher, level)
            results.extend(filtered)
    return results


def get_all_test_cases(module):
    """Return a list of all test case classes defined in a given module."""
    results = []
    for name in dir(module):
        if not name.startswith('Test'):
            continue
        item = getattr(module, name)
        if (isinstance(item, (type, types.ClassType)) and
            issubclass(item, unittest.TestCase)):
            results.append(item)
    return results


def get_test_cases(test_files, cfg, tracer=None):
    """Return a list of test cases from a given list of test modules."""
    matcher = compile_matcher(cfg.test_regex)
    results = []
    startTime = time.time()
    for file in test_files:
        module = import_module(file, cfg, tracer=tracer)
        def get_test_suite ():
            suite = unittest.TestSuite()
            for test_case in get_all_test_cases(module):
                suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
            return suite
        if tracer is not None:
            test_suite = tracer.runfunc(get_test_suite)
        else:
            test_suite = get_test_suite()
        if test_suite is None:
            continue
        if (cfg.level is not None and
            getattr(test_suite, 'level', 0) > cfg.level):
            continue
        filtered = filter_testsuite(test_suite, matcher, cfg.level)
        results.extend(filtered)
    stopTime = time.time()
    timeTaken = float(stopTime - startTime)
    if cfg.print_import_time:
        nmodules = len(test_files)
        plural = (nmodules != 1) and 's' or ''
        print "Imported %d module%s in %.3fs" % (nmodules, plural, timeTaken)
        print
    return results


def extract_tb(tb, limit=None):
    """Improved version of traceback.extract_tb.

    Includes a dict with locals in every stack frame instead of the line.
    """
    list = []
    while tb is not None and (limit is None or len(list) < limit):
        frame = tb.tb_frame
        code = frame.f_code
        name = code.co_name
        filename = code.co_filename
        lineno = tb.tb_lineno
        locals = frame.f_locals
        list.append((filename, lineno, name, locals))
        tb = tb.tb_next
    return list



colorcodes = {'gray': 0, 'red': 1, 'green': 2, 'yellow': 3,
              'blue': 4, 'magenta': 5, 'cyan': 6, 'white': 7}

colormap = {'fail': 'red',
            'warn': 'yellow',
            'pass': 'green',
            'count': 'white',
            'title': 'white',
            'separator': 'dark white',
            'longtestname': 'yellow',
            'filename': 'dark green',
            'lineno': 'green',
            'testname': 'dark yellow',
            'excname': 'red',
            'excstring': 'yellow',
            'tbheader': 'dark white',
            'doctest_ignored': 'gray',
            'doctest_title': 'dark white',
            'doctest_code': 'yellow',
            'doctest_expected': 'green',
            'doctest_got': 'red'}


def colorize(texttype, text):
    """Colorize text by ANSI escape codes in a color provided in colormap."""
    color = colormap[texttype]
    if color.startswith('dark '):
        light = 0
        color = color[len('dark '):] # strip the 'dark' prefix
    else:
        light = 1
    code = 30 + colorcodes[color]
    return '\033[%d;%dm' % (light, code)+ text + '\033[0;0m'


def colorize_exception_only(lines):
    """Colorize result of traceback.format_exception_only."""
    if len(lines) > 1:
        return lines # SyntaxError?  We won't deal with that for now.
    lines = lines[0].splitlines()

    # First, colorize the first line, which usually contains the name
    # and the string of the exception.
    result = []
    # A simple exception.  Try to colorize the first row, leave others be.
    excline = lines[0].split(': ', 1)
    if len(excline) == 2:
        excname = colorize('excname', excline[0])
        excstring = colorize('excstring', excline[1])
        result.append('%s: %s' % (excname, excstring))
    else:
        result.append(colorize('excstring', lines[0]))
    result.extend(lines[1:])
    return '\n'.join(result)


def format_exception(etype, value, tb, limit=None, basedir=None, color=False):
    """Improved version of traceback.format_exception.

    Includes Zope-specific extra information in tracebacks.

    If color is True, ANSI codes are used to colorize output.
    """
    # Show stack trace.
    list = []
    if tb:
        list = ['Traceback (most recent call last):\n']
        if color:
            list[0] = colorize('tbheader', list[0])
        w = list.append

        for filename, lineno, name, locals in extract_tb(tb, limit):
            line = linecache.getline(filename, lineno)
            if color:
                filename = colorize('filename', filename)
                lineno = colorize('lineno', str(lineno))
                name = colorize('testname', name)
                w('  File "%s", line %s, in %s\n' % (filename, lineno, name))
                if line:
                    w('    %s\n' % line.strip())
            else:
                w('  File "%s", line %s, in %s\n' % (filename, lineno, name))
                if line:
                    w('    %s\n' % line.strip())

            tb_info = locals.get('__traceback_info__')
            if tb_info is not None:
                w('  Extra information: %s\n' % repr(tb_info))
            tb_supplement = locals.get('__traceback_supplement__')
            if tb_supplement is not None:
                tb_supplement = tb_supplement[0](*tb_supplement[1:])
                w('  __traceback_supplement__ = %r\n' % (tb_supplement, ))

    # Add the representation of the exception itself.
    lines = traceback.format_exception_only(etype, value)
    if color:
        lines = colorize_exception_only(lines)
    list.extend(lines)

    return list


class CustomTestResult(unittest._TextTestResult):
    """Customised TestResult.

    It can show a progress bar, and displays tracebacks for errors and
    failures as soon as they happen, in addition to listing them all at
    the end.

    Another added feature are configurable resources. Needed resources
    from tests are checked and if denied the test will be skipped.
    """

    __super = unittest._TextTestResult
    __super_init = __super.__init__
    __super_startTest = __super.startTest
    __super_stopTest = __super.stopTest
    __super_printErrors = __super.printErrors
    __super_printErrorList = __super.printErrorList

    def __init__(self, stream, descriptions, verbosity, count, cfg):
        self.__super_init(stream, descriptions, verbosity)
        self.skipped = []
        self.count = count
        self.cfg = cfg
        if cfg.progress:
            self.dots = False
            self._lastWidth = 0
            self._maxWidth = cfg.screen_width - len("xxxx/xxxx (xxx.x%): ") - 1

    def startTest(self, test):
        n = self.testsRun + 1
        if self.cfg.progress:
            # verbosity == 0: 'xxxx/xxxx (xxx.x%)'
            # verbosity == 1: 'xxxx/xxxx (xxx.x%): test name'
            # verbosity >= 2: 'xxxx/xxxx (xxx.x%): test name ... ok'
            self.stream.write("\r%4d" % n)
            if self.count:
                self.stream.write("/%d (%5.1f%%)"
                                  % (self.count, n * 100.0 / self.count))
            if self.showAll: # self.cfg.verbosity == 1
                self.stream.write(": ")
            elif self.cfg.verbosity:
                name = self.getShortDescription(test)
                width = len(name)
                if width < self._lastWidth:
                    name += " " * (self._lastWidth - width)
                self.stream.write(": %s" % name)
                self._lastWidth = width
            self.stream.flush()
        self.__super_startTest(test)  # increments testsRun by one and prints
        self.testsRun = n # override the testsRun calculation
        self.start_time = time.time()

    def getDescription(self, test):
        return test.id() # package.module.class.method

    def getShortDescription(self, test):
        s = test.id() # package.module.class.method
        if len(s) > self._maxWidth:
            namelen = len(s.split('.')[-1])
            left = max(0, (self._maxWidth - namelen) / 2 - 1)
            right = self._maxWidth - left - 3
            s = "%s...%s" % (s[:left], s[-right:])
        return s

    def printErrors(self):
        w = self.stream.writeln
        if self.cfg.progress and not (self.dots or self.showAll):
            w()
        if self.cfg.immediate_errors and (self.errors or self.failures):
            if self.cfg.colorize:
                w(colorize('separator', self.separator1))
                w(colorize('title', "Tests that failed"))
                w(colorize('separator', self.separator2))
            else:
                w(self.separator1)
                w("Tests that failed")
                w(self.separator2)
        self.__super_printErrors()

    def printSkipped (self):
        self.stream.writeln()
        for test, msg in self.skipped:
            self.printSkip(test, msg)

    def printSkip (self, test, msg):
        w = self.stream.writeln
        if self.cfg.colorize:
            c = colorize
        else:
            c = lambda texttype, text: text
        kind = c('warn', "SKIPPED")
        description = c('testname', self.getDescription(test))
        w("%s: %s:" % (kind, description))
        w("         %s" % msg)

    def formatError(self, err):
        return "".join(format_exception(basedir=self.cfg.basedir,
                                        color=self.cfg.colorize, *err))

    def printTraceback(self, kind, test, err):
        w = self.stream.writeln
        if self.cfg.colorize:
            c = colorize
        else:
            c = lambda texttype, text: text
        w()
        w(c('separator', self.separator1))
        kind = c('fail', kind)
        description = c('longtestname', self.getDescription(test))
        w("%s: %s" % (kind, description))
        w(c('separator', self.separator2))
        w(self.formatError(err))
        w()

    def addFailure(self, test, err):
        if self.cfg.immediate_errors:
            self.printTraceback("FAIL", test, err)
        if self.cfg.postmortem:
            pdb.post_mortem(sys.exc_info()[2])
        self.failures.append((test, self.formatError(err)))

    def addError(self, test, err):
        if self.cfg.immediate_errors:
            self.printTraceback("ERROR", test, err)
        if self.cfg.postmortem:
            pdb.post_mortem(sys.exc_info()[2])
        self.errors.append((test, self.formatError(err)))

    def addSkipped(self, test, msg):
        if self.showAll:
            self.stream.writeln("skip")
        elif self.dots:
            self.stream.write("S")
        self.skipped.append((test, msg))

    def addSuccess (self, test):
        now = time.time()
        unittest.TestResult.addSuccess(self, test)
        if self.cfg.colorize:
            c = colorize
        else:
            c = lambda texttype, text: text
        if self.showAll:
            time_taken = float(now - self.start_time)
            time_str = c('count', '%.1f' % time_taken)
            self.stream.writeln("ok (%ss)" % time_str)
        elif self.dots:
            self.stream.write('.')

    def printErrorList(self, flavour, errors):
        if self.cfg.immediate_errors:
            for test, err in errors:
                description = self.getDescription(test)
                self.stream.writeln("%s: %s" % (flavour, description))
        else:
            self.__super_printErrorList(flavour, errors)


def get_tc_priv (testcase, attr):
    """
    get mangled private variables of TestCase instances
    """
    if sys.version_info >= (2, 5, 0, 'alpha', 1):
        return getattr(testcase, "_" + attr)
    return getattr(testcase, "_TestCase__" + attr)


class CustomTestCase (unittest.TestCase):
    """
    A test case with improved inequality test and resource support.
    """

    def denied_resources (self, cfg_resources):
        resources = getattr(self, "needed_resources", [])
        return [x for x in resources if x not in cfg_resources]

    def run (self, result=None):
        if not isinstance(result, CustomTestResult):
            raise ValueError("Needed CustomTestResult object: %r" % result)
        result.startTest(self)
        testMethod = getattr(self, get_tc_priv(self, "testMethodName"))
        try:
            denied = self.denied_resources(result.cfg.resources)
            if denied:
                res = ",".join(["%r" % x for x in denied])
                s = len(denied) != 1 and "s" or ""
                msg = "missing resource%s %s" % (s, res)
                result.addSkipped(self, msg)
                return
            try:
                self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, get_tc_priv(self, "exc_info")())
                return

            ok = False
            try:
                testMethod()
                ok = True
            except self.failureException:
                result.addFailure(self, get_tc_priv(self, "exc_info")())
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, get_tc_priv(self, "exc_info")())

            try:
                self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, get_tc_priv(self, "exc_info")())
                ok = False
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)

    def failUnlessEqual (self, first, second, msg=None):
        """
        Define the first argument as the test value, and the second
        one as the excpected value. Adjust the default error message
        accordingly.
        """
        if msg is None:
            r1 = repr(first)
            r2 = repr(second)
            if len(r1) > 40 or len(r2) > 40:
                sep = "\n"
            else:
                sep = ", "
            msg = "got %s%sexpected %s" % (r1, sep, r2)
        super(CustomTestCase, self).failUnlessEqual(first, second, msg=msg)

    assertEqual = assertEquals = failUnlessEqual

unittest.TestCase = CustomTestCase


class CustomTestRunner(unittest.TextTestRunner):
    """Customised TestRunner.

    See CustomisedTextResult for a list of extensions.
    """

    __super = unittest.TextTestRunner
    __super_init = __super.__init__
    __super_run = __super.run

    def __init__(self, cfg, stream=sys.stdout, count=None):
        self.__super_init(verbosity=cfg.verbosity, stream=stream)
        self.cfg = cfg
        self.count = count

    def run(self, test):
        """Run the given test case or test suite."""
        if self.count is None:
            self.count = test.countTestCases()
        if self.cfg.colorize:
            c = colorize
        else:
            c = lambda texttype, text: text
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = float(stopTime - startTime)
        result.printSkipped()
        result.printErrors()
        run = result.testsRun
        if not self.cfg.quiet:
            self.stream.writeln(c('separator', result.separator2))
            run_str = c('count', str(run))
            time_str = c('count', '%.1f' % timeTaken)
            self.stream.writeln("Ran %s test%s in %ss" %
                                (run_str, run != 1 and "s" or "", time_str))
            self.stream.writeln()
        if result.skipped:
            self.stream.write(c('warn', "SKIPPED TESTS"))
            count = c('count', str(len(result.skipped)))
            self.stream.writeln(" (%s)" % count)
        if not result.wasSuccessful():
            self.stream.write(c('fail', "FAILED"))

            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                self.stream.write(" (failures=%s" % c('count', str(failed)))
            if errored:
                if failed: self.stream.write(", ")
                else: self.stream.write("(")
                self.stream.write("errors=%s" % c('count', str(errored)))
            self.stream.writeln(")")
        elif not self.cfg.quiet:
            self.stream.writeln(c('pass', "OK"))
        return result

    def _makeResult(self):
        return CustomTestResult(self.stream, self.descriptions, self.verbosity,
                                cfg=self.cfg, count=self.count)

def run_tests (cfg, test_cases, tracer):
    from django.test import utils
    from django.conf import settings
    runner = CustomTestRunner(cfg, count=len(test_cases))
    utils.setup_test_environment()
    suite = unittest.TestSuite()
    suite.addTests(test_cases)
    old_name = settings.DATABASE_NAME
    utils.create_test_db(0, autoclobber=True)
    if tracer is not None:
        success = tracer.runfunc(runner.run, suite).wasSuccessful()
        results = tracer.results()
        results.write_results(show_missing=True, coverdir=cfg.coverdir)
    else:
        if cfg.profile:
            import hotshot
            prof = hotshot.Profile("unittesttest.prof")
            prof.start()
        success = runner.run(suite).wasSuccessful()
        if cfg.profile:
            prof.stop()
    utils.destroy_test_db(old_name, 0)
    utils.teardown_test_environment()


def main(argv):
    """Main program."""
    # Environment
    if sys.version_info < (2, 3):
        print >> sys.stderr, '%s: need Python 2.3 or later' % argv[0]
        print >> sys.stderr, 'your python is %s' % sys.version
        return 1

    # Defaults
    cfg = Options()
    if not cfg.basedir:
        cfg.basedir = os.path.abspath(os.path.dirname(argv[0]))

    # Figure out terminal size
    try:
        import curses
    except ImportError:
        pass
    else:
        try:
            curses.setupterm()
            cols = curses.tigetnum('cols')
            if cols > 0:
                cfg.screen_width = cols
        except curses.error:
            pass

    # Option processing
    try:
        opts, args = getopt.gnu_getopt(argv[1:], 'hvpcqwd1s:',
                               ['list-files', 'list-tests',
                                'level=', 'all-levels', 'coverage',
                                'search-in=', 'immediate-errors',
                                'delayed-errors', 'help',
                                'resource=', 'profile',
                               ])
    except getopt.error, e:
        print >> sys.stderr, '%s: %s' % (argv[0], e)
        print >> sys.stderr, 'run %s -h for help' % argv[0]
        return 1
    for k, v in opts:
        if k in ['-h', '--help']:
            print __doc__
            return 0
        elif k == '-v':
            cfg.verbosity += 1
            cfg.quiet = False
        elif k == '-p':
            cfg.progress = True
            cfg.quiet = False
        elif k == '-c':
            cfg.colorize = True
        elif k == '-q':
            cfg.verbosity = 0
            cfg.progress = False
            cfg.quiet = True
        elif k == '-d':
            cfg.postmortem = True
        elif k == '-1':
            cfg.first_doctest_failure = True
        elif k == '--list-files':
            cfg.list_files = True
            cfg.run_tests = False
        elif k == '--list-tests':
            cfg.list_tests = True
            cfg.run_tests = False
        elif k == '--coverage':
            cfg.coverage = True
        elif k == '--profile':
            cfg.profile = True
        elif k == '--resource':
            cfg.resources.append(v)
        elif k == '--level':
            try:
                cfg.level = int(v)
            except ValueError:
                print >> sys.stderr, '%s: invalid level: %s' % (argv[0], v)
                print >> sys.stderr, 'run %s -h for help' % argv[0]
                return 1
        elif k == '--all-levels':
            cfg.level = None
        elif k in ('-s', '--search-in'):
            if not v.startswith(cfg.basedir):
                print >> sys.stderr, ('%s: argument to --search-in (%s) must'
                                      ' be a subdir of %s'
                                      % (argv[0], v, cfg.basedir))
                return 1
            cfg.search_in += (v, )
        elif k == '--immediate-errors':
            cfg.immediate_errors = True
        elif k == '--delayed-errors':
            cfg.immediate_errors = False
        else:
            print >> sys.stderr, '%s: invalid option: %s' % (argv[0], k)
            print >> sys.stderr, 'run %s -h for help' % argv[0]
            return 1
    if args:
        cfg.pathname_regex = args[0]
    if len(args) > 1:
        cfg.test_regex = args[1]
    if len(args) > 2:
        print >> sys.stderr, '%s: too many arguments: %s' % (argv[0], args[2])
        print >> sys.stderr, 'run %s -h for help' % argv[0]
        return 1

    if not cfg.search_in:
        cfg.search_in = (cfg.basedir, )

    # Do not print "Imported %d modules in %.3fs" if --list-* was specified
    # or if quiet mode is enabled.
    if cfg.quiet or cfg.list_tests or cfg.list_files:
        cfg.print_import_time = False

    # Set up the python path
    sys.path[0] = cfg.basedir

    # Set up tracing before we start importing things
    tracer = None
    if cfg.run_tests and cfg.coverage:
        import trace
        # trace.py in Python 2.3.1 is buggy:
        # 1) Despite sys.prefix being in ignoredirs, a lot of system-wide
        #    modules are included in the coverage reports
        # 2) Some module file names do not have the first two characters,
        #    and in general the prefix used seems to be arbitrary
        # These bugs are fixed in src/trace.py which should be in PYTHONPATH
        # before the official one.
        ignoremods = ['test']
        ignoredirs = [sys.prefix, sys.exec_prefix]
        tracer = trace.Trace(count=True, trace=False,
                    ignoremods=ignoremods, ignoredirs=ignoredirs)

    # Finding and importing
    test_files = get_test_files(cfg)
    if cfg.list_tests or cfg.run_tests:
        test_cases = get_test_cases(test_files, cfg, tracer=tracer)

    # Configure doctests
    if cfg.first_doctest_failure:
        import doctest
        # The doctest module in Python 2.3 does not have this feature
        if hasattr(doctest, 'REPORT_ONLY_FIRST_FAILURE'):
            doctest.set_unittest_reportflags(doctest.REPORT_ONLY_FIRST_FAILURE)

    # Configure the logging module
    import logging
    logging.basicConfig()
    logging.root.setLevel(logging.CRITICAL)

    # Running
    success = True
    if cfg.list_files:
        baselen = len(cfg.basedir) + 1
        print "\n".join([fn[baselen:] for fn in test_files])
    if cfg.list_tests:
        print "\n".join([test.id() for test in test_cases])
    if cfg.run_tests:
        run_tests(cfg, test_cases, tracer)

    # That's all
    if success:
        return 0
    else:
        return 1


if __name__ == '__main__':
    exitcode = main(sys.argv)
    sys.exit(exitcode)
