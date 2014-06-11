LinkChecker
============

[![Build Status](https://travis-ci.org/valdergallo/django-compress-storage.png?branch=master)](https://travis-ci.org/valdergallo/django-compress-storage)
[![Latest Version](http://img.shields.io/pypi/v/django-compress-storage.svg)](https://pypi.python.org/pypi/django-compress-storage)
[![BSD License](http://img.shields.io/badge/license-BSD-yellow.svg)](http://opensource.org/licenses/BSD-3-Clause)

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
- a command line, GUI and web interface
- various check plugins available, eg. HTML syntax and antivirus checks.

Installation
-------------
See doc/install.txt in the source code archive.

Usage
------
Execute ``linkchecker http://www.example.com``.
For other options see ``linkchecker --help``.
