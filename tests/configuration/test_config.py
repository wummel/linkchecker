# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2014 Bastian Kleineidam
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Test config parsing.
"""

import unittest
import os
import linkcheck.configuration


def get_file (filename=None):
    """Get file name located within 'data' directory."""
    directory = os.path.join("tests", "configuration", "data")
    if filename:
        return unicode(os.path.join(directory, filename))
    return unicode(directory)


class TestConfig (unittest.TestCase):
    """Test configuration parsing."""

    def test_confparse (self):
        config = linkcheck.configuration.Configuration()
        files = [get_file("config0.ini")]
        config.read(files)
        config.sanitize()
        # checking section
        for scheme in ("http", "https", "ftp"):
            self.assertTrue(scheme in config["allowedschemes"])
        self.assertEqual(config["threads"], 5)
        self.assertEqual(config["timeout"], 42)
        self.assertEqual(config["aborttimeout"], 99)
        self.assertEqual(config["recursionlevel"], 1)
        self.assertEqual(config["nntpserver"], "example.org")
        self.assertEqual(config["cookiefile"], "blablabla")
        self.assertEqual(config["useragent"], "Example/0.0")
        self.assertEqual(config["debugmemory"], 1)
        self.assertEqual(config["localwebroot"], "foo")
        self.assertEqual(config["sslverify"], "/path/to/cacerts.crt")
        self.assertEqual(config["maxnumurls"], 1000)
        self.assertEqual(config["maxrunseconds"], 1)
        self.assertEqual(config["maxfilesizeparse"], 100)
        self.assertEqual(config["maxfilesizedownload"], 100)
        # filtering section
        patterns = [x["pattern"].pattern for x in config["externlinks"]]
        for prefix in ("ignore_", "nofollow_"):
            for suffix in ("1", "2"):
                key = "%simadoofus%s" % (prefix, suffix)
                self.assertTrue(key in patterns)
        for key in ("url-unicode-domain",):
            self.assertTrue(key in config["ignorewarnings"])
        self.assertTrue(config["checkextern"])
        # authentication section
        patterns = [x["pattern"].pattern for x in config["authentication"]]
        for suffix in ("1", "2"):
            key = "imadoofus%s" % suffix
            self.assertTrue(key in patterns)
        self.assertTrue("http://www.example.com/" in patterns)
        self.assertTrue("http://www.example.com/nopass" in patterns)
        self.assertEqual(config["loginurl"], "http://www.example.com/")
        self.assertEqual(config["loginuserfield"], "mylogin")
        self.assertEqual(config["loginpasswordfield"], "mypassword")
        self.assertEqual(config["loginextrafields"]["name1"], "value1")
        self.assertEqual(config["loginextrafields"]["name 2"], "value 2")
        self.assertEqual(len(config["loginextrafields"]), 2)
        # output section
        self.assertTrue(linkcheck.log.is_debug(linkcheck.LOG_THREAD))
        self.assertFalse(config["status"])
        self.assertTrue(isinstance(config["logger"], linkcheck.logger.customxml.CustomXMLLogger))
        self.assertTrue(config["verbose"])
        self.assertTrue(config["warnings"])
        self.assertFalse(config["quiet"])
        self.assertEqual(len(config["fileoutput"]), 8)
        # plugins
        for plugin in ("AnchorCheck", "CssSyntaxCheck", "HtmlSyntaxCheck", "LocationInfo", "RegexCheck", "SslCertificateCheck", "VirusCheck", "HttpHeaderInfo"):
            self.assertTrue(plugin in config["enabledplugins"])
        # text logger section
        self.assertEqual(config["text"]["filename"], "imadoofus.txt")
        self.assertEqual(config["text"]["parts"], ["realurl"])
        self.assertEqual(config["text"]["encoding"], "utf-8")
        self.assertEqual(config["text"]["colorparent"], "blink;red")
        self.assertEqual(config["text"]["colorurl"], "blink;red")
        self.assertEqual(config["text"]["colorname"], "blink;red")
        self.assertEqual(config["text"]["colorreal"], "blink;red")
        self.assertEqual(config["text"]["colorbase"], "blink;red")
        self.assertEqual(config["text"]["colorvalid"], "blink;red")
        self.assertEqual(config["text"]["colorinvalid"], "blink;red")
        self.assertEqual(config["text"]["colorinfo"], "blink;red")
        self.assertEqual(config["text"]["colorwarning"], "blink;red")
        self.assertEqual(config["text"]["colordltime"], "blink;red")
        self.assertEqual(config["text"]["colorreset"], "blink;red")
        # gml logger section
        self.assertEqual(config["gml"]["filename"], "imadoofus.gml")
        self.assertEqual(config["gml"]["parts"], ["realurl"])
        self.assertEqual(config["gml"]["encoding"], "utf-8")
        # dot logger section
        self.assertEqual(config["dot"]["filename"], "imadoofus.dot")
        self.assertEqual(config["dot"]["parts"], ["realurl"])
        self.assertEqual(config["dot"]["encoding"], "utf-8")
        # csv logger section
        self.assertEqual(config["csv"]["filename"], "imadoofus.csv")
        self.assertEqual(config["csv"]["parts"], ["realurl"])
        self.assertEqual(config["csv"]["encoding"], "utf-8")
        self.assertEqual(config["csv"]["separator"], ";")
        self.assertEqual(config["csv"]["quotechar"], "'")
        # sql logger section
        self.assertEqual(config["sql"]["filename"], "imadoofus.sql")
        self.assertEqual(config["sql"]["parts"], ["realurl"])
        self.assertEqual(config["sql"]["encoding"], "utf-8")
        self.assertEqual(config["sql"]["separator"], ";")
        self.assertEqual(config["sql"]["dbname"], "linksdb")
        # html logger section
        self.assertEqual(config["html"]["filename"], "imadoofus.html")
        self.assertEqual(config["html"]["parts"], ["realurl"])
        self.assertEqual(config["html"]["encoding"], "utf-8")
        self.assertEqual(config["html"]["colorbackground"], "#ff0000")
        self.assertEqual(config["html"]["colorurl"], "#ff0000")
        self.assertEqual(config["html"]["colorborder"], "#ff0000")
        self.assertEqual(config["html"]["colorlink"], "#ff0000")
        self.assertEqual(config["html"]["colorwarning"], "#ff0000")
        self.assertEqual(config["html"]["colorerror"], "#ff0000")
        self.assertEqual(config["html"]["colorok"], "#ff0000")
        # blacklist logger section
        self.assertEqual(config["blacklist"]["filename"], "blacklist")
        self.assertEqual(config["blacklist"]["encoding"], "utf-8")
        # xml logger section
        self.assertEqual(config["xml"]["filename"], "imadoofus.xml")
        self.assertEqual(config["xml"]["parts"], ["realurl"])
        self.assertEqual(config["xml"]["encoding"], "utf-8")
        # gxml logger section
        self.assertEqual(config["gxml"]["filename"], "imadoofus.gxml")
        self.assertEqual(config["gxml"]["parts"], ["realurl"])
        self.assertEqual(config["gxml"]["encoding"], "utf-8")

    def test_confparse_error1 (self):
        config = linkcheck.configuration.Configuration()
        files = [get_file("config1.ini")]
        self.assertRaises(linkcheck.LinkCheckerError, config.read, files)

    def test_confparse_error2 (self):
        config = linkcheck.configuration.Configuration()
        files = [get_file("config2.ini")]
        self.assertRaises(linkcheck.LinkCheckerError, config.read, files)
