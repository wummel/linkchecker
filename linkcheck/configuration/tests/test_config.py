# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2008 Bastian Kleineidam
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
Test config parsing.
"""

import unittest
import os
import linkcheck.configuration


def get_file (filename=None):
    """Get file name located within 'data' directory."""
    directory = os.path.join("linkcheck", "configuration", "tests", "data")
    if filename:
        return unicode(os.path.join(directory, filename))
    return unicode(directory)


class TestConfig (unittest.TestCase):
    """Test configuration parsing."""

    def test_confparse (self):
        """Check url validity."""
        config = linkcheck.configuration.Configuration()
        files = [get_file("config0.ini")]
        config.read(files)
        # checking section
        self.assertEqual(config["threads"], 5)
        self.assertEqual(config["timeout"], 42)
        self.assertFalse(config["anchors"])
        self.assertEqual(config["recursionlevel"], 1)
        self.assertEqual(config["warningregex"].pattern, "Oracle DB Error")
        self.assertEqual(config["warnsizebytes"], 2000)
        self.assertEqual(config["nntpserver"], "example.org")
        self.assertTrue(config["anchorcaching"])
        # filtering section
        patterns = [x["pattern"].pattern for x in config["externlinks"]]
        for prefix1 in ("ignore_", "nofollow_"):
            for prefix2 in ("", "old"):
                for suffix in ("1", "2"):
                    key  = "%s%simadoofus%s" % (prefix1, prefix2, suffix)
                    self.assertTrue(key in patterns)
        patterns = [x.pattern for x in config["noproxyfor"]]
        for prefix1 in ("noproxyfor_",):
            for prefix2 in ("", "old"):
                for suffix in ("1", "2"):
                    key  = "%s%simadoofus%s" % (prefix1, prefix2, suffix)
                    self.assertTrue(key in patterns)
        for key in ("url-unnormed","url-unicode-domain","anchor-not-found"):
            self.assertTrue(key in config["ignorewarnings"])
        # authentication section
        patterns = [x["pattern"].pattern for x in config["authentication"]]
        for prefix in ("", "old"):
            for suffix in ("1", "2"):
                key = "%simadoofus%s" % (prefix, suffix)
                self.assertTrue(key in patterns)
        # output section
        self.assertTrue(config["interactive"])
        self.assertTrue(linkcheck.log.is_debug(linkcheck.LOG_THREAD))
        self.assertFalse(config["status"])
        self.assertTrue(isinstance(config["logger"], linkcheck.logger.Loggers["xml"]))
        self.assertTrue(config["verbose"])
        self.assertTrue(config["warnings"])
        self.assertFalse(config["quiet"])
        self.assertEqual(len(config["fileoutput"]), 8)
        # logger config sections
        # XXX todo

    def test_confparse_error1 (self):
        config = linkcheck.configuration.Configuration()
        files = [get_file("config1.ini")]
        self.assertRaises(linkcheck.LinkCheckerError, config.read, files)

    def test_confparse_error2 (self):
        config = linkcheck.configuration.Configuration()
        files = [get_file("config2.ini")]
        self.assertRaises(linkcheck.LinkCheckerError, config.read, files)


def test_suite ():
    """Build and return a TestSuite."""
    return unittest.makeSuite(TestConfig)


if __name__ == '__main__':
    unittest.main()
