# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2006 Bastian Kleineidam
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
Define standard test support classes funtional for LinkChecker tests.
"""

import os
import re
import codecs
import difflib
import unittest

import linkcheck
import linkcheck.checker
import linkcheck.configuration
import linkcheck.logger


class TestLogger (linkcheck.logger.Logger):
    """
    Output logger for automatic regression tests.
    """

    def __init__ (self, **kwargs):
        """
        The kwargs must have "expected" keyword with the expected logger
        output lines.
        """
        super(TestLogger, self).__init__(**kwargs)
        # list of expected output lines
        self.expected = kwargs['expected']
        # list of real output lines
        self.result = []
        # diff between expected and real output
        self.diff = []

    def start_output (self):
        """
        Nothing to do here.
        """
        pass

    def log_url (self, url_data):
        """
        Append logger output to self.result.
        """
        if self.has_part('url'):
            url = u"url %s" % (url_data.base_url or u"")
            if url_data.cached:
                url += u" (cached)"
            self.result.append(url)
        if self.has_part('cachekey'):
            self.result.append(u"cache key %s" % url_data.cache_url_key)
        if self.has_part('realurl'):
            self.result.append(u"real url %s" % url_data.url)
        if self.has_part('name') and url_data.name:
            self.result.append(u"name %s" % url_data.name)
        if self.has_part('base') and url_data.base_ref:
            self.result.append(u"baseurl %s" % url_data.base_ref)
        if self.has_part('info'):
            for info in url_data.info:
                line = info[1]
                if "Last modified" not in line and \
                   "is located in" not in line:
                    self.result.append(u"info %s" % line)
        if self.has_part('warning'):
            for warning in url_data.warnings:
                self.result.append(u"warning %s" % warning[1])
        if self.has_part('result'):
            self.result.append(url_data.valid and u"valid" or u"error")
        # note: do not append url_data.result since this is
        # platform dependent

    def end_output (self, linknumber=-1):
        """
        Stores differences between expected and result in self.diff.
        """
        for line in difflib.unified_diff(self.expected, self.result):
            if not isinstance(line, unicode):
                line = unicode(line, "iso8859-1", "ignore")
            self.diff.append(line)


def get_file (filename=None):
    """
    Get file name located within 'data' directory.
    """
    directory = os.path.join("linkcheck", "checker", "tests", "data")
    if filename:
        return unicode(os.path.join(directory, filename))
    return unicode(directory)


def get_file_url (filename):
    return re.sub("^([a-zA-Z]):", r"/\1|", filename.replace("\\", "/"))


def add_fileoutput_config (config):
    if os.name == 'posix':
        devnull = '/dev/null'
    elif os.name == 'nt':
        devnull = 'NUL'
    else:
        return
    for ftype in linkcheck.Loggers.keys():
        if ftype in ('test', 'blacklist'):
            continue
        logger = config.logger_new(ftype, fileoutput=1, filename=devnull)
        config['fileoutput'].append(logger)


def get_test_aggregate (confargs, logargs):
    """
    Initialize a test configuration object.
    """
    config = linkcheck.configuration.Configuration()
    config.logger_add('test', TestLogger)
    config['recursionlevel'] = 1
    config['logger'] = config.logger_new('test', **logargs)
    add_fileoutput_config(config)
    # uncomment for debugging
    #config.init_logging(debug=["all"])
    config["anchors"] = True
    config["verbose"] = True
    config['threads'] = 0
    config['status'] = False
    config['cookies'] = True
    config.update(confargs)
    return linkcheck.director.get_aggregate(config)


class LinkCheckTest (unittest.TestCase):
    """
    Functional test class with ability to test local files.
    """

    def norm (self, url):
        """
        Helper function to norm a url.
        """
        return linkcheck.url.url_norm(url)[0]

    def get_resultlines (self, filename):
        """
        Return contents of file, as list of lines without line endings,
        ignoring empty lines and lines starting with a hash sign (#).
        """
        resultfile = get_file(filename+".result")
        d = {'curdir': get_file_url(os.getcwd()),
             'datadir': get_file_url(get_file()),
            }
        f = codecs.open(resultfile, "r", "iso-8859-15")
        resultlines = [line.rstrip('\r\n') % d for line in f \
                       if line.strip() and not line.startswith(u'#')]
        f.close()
        return resultlines

    def file_test (self, filename, confargs=None, assume_local=True):
        """
        Check <filename> with expected result in <filename>.result.
        """
        url = get_file(filename)
        if confargs is None:
            confargs = {}
        logargs = {'expected': self.get_resultlines(filename)}
        aggregate = get_test_aggregate(confargs, logargs)
        url_data = linkcheck.checker.get_url_from(
                                url, 0, aggregate, assume_local=assume_local)
        if assume_local:
            linkcheck.add_intern_pattern(url_data, aggregate.config)
        aggregate.urlqueue.put(url_data)
        linkcheck.director.check_urls(aggregate)
        diff = aggregate.config['logger'].diff
        if diff:
            sep = unicode(os.linesep)
            l = [url] + diff
            l = sep.join(l)
            self.fail(l.encode("iso8859-1", "ignore"))

    def direct (self, url, resultlines, parts=None, recursionlevel=0,
                confargs=None, assume_local=False):
        """
        Check url with expected result.
        """
        assert isinstance(url, unicode), repr(url)
        if confargs is None:
            confargs = {'recursionlevel': recursionlevel}
        else:
            confargs['recursionlevel'] = recursionlevel
        logargs = {'expected': resultlines}
        if parts is not None:
            logargs['parts'] = parts
        aggregate = get_test_aggregate(confargs, logargs)
        url_data = linkcheck.checker.get_url_from(
                                url, 0, aggregate, assume_local=assume_local)
        if assume_local:
            linkcheck.add_intern_pattern(url_data, aggregate.config)
        aggregate.urlqueue.put(url_data)
        linkcheck.director.check_urls(aggregate)
        diff = aggregate.config['logger'].diff
        if diff:
            sep = unicode(os.linesep)
            l = [u"Differences found testing %s" % url]
            l.extend(x.rstrip() for x in diff[2:])
            self.fail(sep.join(l).encode("iso8859-1", "ignore"))

