# -*- coding: iso-8859-1 -*-
"""define standard test support classes funtional for LinkChecker tests"""
# Copyright (C) 2004  Bastian Kleineidam
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

import os
import unittest
import difflib

import linkcheck
import linkcheck.checker
import linkcheck.checker.cache
import linkcheck.checker.consumer
import linkcheck.configuration
import linkcheck.logger


class TestLogger (linkcheck.logger.Logger):
    """Output logger for automatic regression tests"""

    def __init__ (self, **kwargs):
        """kwargs must have "expected" keyword with the expected logger
           output lines"""
        super(TestLogger, self).__init__(**kwargs)
        self.expected = kwargs['expected']
        self.result = []
        self.diff = []

    def start_output (self):
        """nothing to do here"""
        pass

    def new_url (self, url_data):
        """append logger output to self.result"""
        if self.has_field('url'):
            url = "url %r" % url_data.base_url
            if url_data.cached:
                url += " (cached)"
            self.result.append(url)
        if self.has_field('cachekey'):
            self.result.append("cache key %s" % url_data.cache_url_key)
        if self.has_field('realurl'):
            self.result.append("real url %s" % url_data.url)
        if self.has_field('name') and url_data.name:
            self.result.append("name %s" % url_data.name)
        if self.has_field('base') and url_data.base_ref:
            self.result.append("baseurl %s" % url_data.base_ref)
        if self.has_field('info'):
            for info in url_data.info:
                self.result.append("info %s" % info)
        if self.has_field('warning'):
            for warning in url_data.warning:
                self.result.append("warning %s" % warning)
        if self.has_field('result'):
            self.result.append(url_data.valid and "valid" or "error")
        # note: do not append url_data.result since this is
        # platform dependent

    def end_output (self, linknumber=-1):
        """stores differences between expected and result in self.diff"""
        for line in difflib.unified_diff(self.expected, self.result):
            self.diff.append(line)


def get_test_consumer (confargs, logargs):
    """initialize a test configuration object"""
    config = linkcheck.configuration.Configuration()
    config.logger_add('test', TestLogger)
    config['recursionlevel'] = 1
    config['logger'] = config.logger_new('test', **logargs)
    config["anchors"] = True
    config["verbose"] = True
    config['threads'] = 0
    for key, value in confargs.items():
        config[key] = value
    cache = linkcheck.checker.cache.Cache()
    return linkcheck.checker.consumer.Consumer(config, cache)


class StandardTest (unittest.TestCase):
    """functional test class with ability to test local files"""

    def setUp (self):
        """check resources, using the provided function
           check_resources() from test.py
        """
        if hasattr(self, "needed_resources"):
            self.check_resources(self.needed_resources)

    def quote (self, url):
        """helper function quote a url"""
        return linkcheck.url.url_norm(url)

    def get_file (self, filename):
        """get file name located within 'data' directory"""
        return os.path.join("linkcheck", "ftests", "data", filename)

    def get_resultlines (self, filename):
        """return contents of file, as list of lines without line endings,
           ignoring empty lines and lines starting with a hash sign (#).
        """
        resultfile = self.get_file(filename+".result")
        f = open(resultfile)
        resultlines = [line.rstrip('\r\n') % {'curdir': os.getcwd()} \
                       for line in f \
                       if line.strip() and not line.startswith('#')]
        f.close()
        return resultlines

    def file_test (self, filename):
        """check <filename> with expected result in <filename>.result"""
        url = self.get_file(filename)
        confargs = {}
        logargs = {'expected': self.get_resultlines(filename)}
        consumer = get_test_consumer(confargs, logargs)
        url_data = linkcheck.checker.get_url_from(
                                      url, 0, consumer, cmdline=True)
        consumer.append_url(url_data)
        linkcheck.checker.check_urls(consumer)
        if consumer.config['logger'].diff:
            self.fail(os.linesep.join([url] + consumer.config['logger'].diff))

    def direct (self, url, resultlines, fields=None, recursionlevel=0):
        """check url with expected result"""
        confargs = {'recursionlevel': recursionlevel}
        logargs = {'expected': resultlines}
        if fields is not None:
            logargs['fields'] = fields
        consumer = get_test_consumer(confargs, logargs)
        url_data = linkcheck.checker.get_url_from(url, 0, consumer)
        consumer.append_url(url_data)
        linkcheck.checker.check_urls(consumer)
        if consumer.config['logger'].diff:
            self.fail(os.linesep.join([url] + consumer.config['logger'].diff))
