LinkChecker
============

|Build Status|_ |Latest Version|_ |License|_

.. |Build Status| image:: https://travis-ci.org/wummel/linkchecker.svg?branch=master
.. _Build Status: https://travis-ci.org/wummel/linkchecker
.. |Latest Version| image:: http://img.shields.io/pypi/v/LinkChecker.svg
.. _Latest Version: https://pypi.python.org/pypi/LinkChecker
.. |License| image:: http://img.shields.io/badge/license-GPL2-d49a6a.svg
.. _License: http://opensource.org/licenses/GPL-2.0

Check for broken links in web sites.

Features
---------

- recursive and multithreaded checking and site crawling
- output in colored or normal text, HTML, SQL, CSV, XML or a sitemap graph in different formats
- HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Telnet and local file links support
- restrict link checking with regular expression filters for URLs
- proxy support
- username/password authorization for HTTP, FTP and Telnet
- honors robots.txt exclusion protocol
- Cookie support
- HTML5 support
- a command line and web interface
- various check plugins available, eg. HTML syntax and antivirus checks.

Installation
-------------
See doc/install.txt in the source code archive.
Python 2.7.2 or later is needed.

Usage
------
Execute ``linkchecker http://www.example.com``.
For other options see ``linkchecker --help``.
