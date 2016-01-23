title: Check websites for broken links
---

Introduction
-------------
LinkChecker is a free, [GPL](http://www.gnu.org/licenses/gpl-2.0.html)
licensed website validator.
LinkChecker checks links in web documents or full websites.
It runs on Python 2 systems, requiring Python 2.7.2 or later.
Python 3 is not (yet) supported.


Features
---------

- recursive and multithreaded checking and site crawling
- output in colored or normal text, HTML, SQL, CSV, XML or a sitemap
  graph in different formats
- HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Telnet and local file
  links support
- restriction of link checking with regular expression filters for URLs
- proxy support
- username/password authorization for HTTP and FTP and Telnet
- honors robots.txt exclusion protocol
- Cookie support
- HTML5 support
- [Plugin support](plugins.html)
  allowing custom page checks. Currently available are 
  HTML and CSS syntax checks, Antivirus checks, and more.
- Different interfaces: command line and web interface
- ... and a lot more check options documented in the
  [manual page](man1/linkchecker.1.html).


Screenshots
------------

[![CLI screenshot](images/shot1_thumb.jpg)](images/shot1.png) | [![CGI screenshot](images/shot3_thumb.jpg)](images/shot3.png)
--------------------------------------------------------------|--------------------------------------------------------------
Commandline interface                                         | CGI web interface

Basic usage
------------
To check a URL like `http://www.example.org/myhomepage/` it is enough to
enter `http://www.example.org/myhomepage/` in the web interface, or execute
`linkchecker http://www.example.org/myhomepage/` on the command line.

This check will validate recursively all pages starting with
`http://www.example.org/myhomepage/`. Additionally, all external links
pointing outside of `www.example.org` will be checked but not recursed
into.

Other linkcheckers
-------------------
If this software does not fit your requirements, you can check out
[other free linkcheckers](other.html).


Test suite status
------------------
Linkchecker has extensive unit tests to ensure code quality.
[Travis CI](https://travis-ci.org/) is used for continuous build
and test integration.

[![Build Status](https://travis-ci.org/wummel/linkchecker.png)](https://travis-ci.org/wummel/linkchecker)
