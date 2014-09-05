title: "Frequently asked questions"
---
**Q: LinkChecker produced an error, but my web page is ok with
Mozilla/IE/Opera/... Is this a bug in LinkChecker?**

A: Please check your web pages first. Are they really ok?
Often the major browsers are very forgiving and good at handling HTML
of HTTP errors, while LinkChecker complains in most cases of invalid
content.

Use the `--check-html` option, or check if you are using a proxy
which produces the error.

**Q: I still get an error, but the page is definitely ok.**

A: Some servers deny access of automated tools (also called robots)
like LinkChecker. This is not a bug in LinkChecker but rather a
policy by the webmaster running the website you are checking. Look in
the ``/robots.txt`` file which follows the
[robots.txt exclusion standard](http://www.robotstxt.org/robotstxt.html).

For identification LinkChecker adds to each request a User-Agent header
like this:

    Mozilla/5.0 (compatible; LinkChecker/9.3; +http://wummel.github.io/linkchecker/)

If you yourself are the webmaster, consider allowing LinkChecker to
check your web pages by adding the following to your robots.txt file:

    User-Agent: LinkChecker
    Allow: /

**Q: How can I tell LinkChecker which proxy to use?**

A: LinkChecker works automatically with proxies. In a Unix or Windows
environment, set the http_proxy, https_proxy, ftp_proxy environment
variables to a URL that identifies the proxy server before starting
LinkChecker. For example

    $ http_proxy="http://www.example.com:3128"
    $ export http_proxy


**Q: The link "mailto:john@company.com?subject=Hello John" is reported
as an error.**

A: You have to quote special characters (e.g. spaces) in the subject field.
The correct link should be "mailto:...?subject=Hello%20John"
Unfortunately browsers like IE and Netscape do not enforce this.


**Q: Has LinkChecker JavaScript support?**

A: No, it never will. If your page is only working with JS, it is
better to use a browser testing tool like [Selenium](http://seleniumhq.org/).


**Q: Is the LinkCheckers cookie feature insecure?**

A: Potentially yes. This depends on what information you specify in the
cookie file. The cookie information will be sent to the specified
hosts.

Also, the following restrictions apply for cookies that LinkChecker
receives from the hosts it check:

- Cookies will only be sent back to the originating server (ie. no
  third party cookies are allowed).
- Cookies are only stored in memory. After LinkChecker finishes, they
  are lost.
- The cookie feature is disabled as default.


**Q: LinkChecker retrieves a /robots.txt file for every site it
checks. What is that about?**

A: LinkChecker follows the
[robots.txt exclusion standard](http://www.robotstxt.org/robotstxt.html).
To avoid misuse of LinkChecker, you cannot turn this feature off.
See the [Web Robot pages](http://www.robotstxt.org/robotstxt.html) and the
[Spidering report](http://www.w3.org/Search/9605-Indexing-Workshop/ReportOutcomes/Spidering.txt)
for more info.

If you yourself are the webmaster, consider allowing LinkChecker to
check your web pages by adding the following to your robots.txt file:

    User-Agent: LinkChecker
    Allow: /


**Q: How do I print unreachable/dead documents of my website with
LinkChecker?**

A: No can do. This would require file system access to your web
repository and access to your web server configuration.


**Q: How do I check HTML/XML/CSS syntax with LinkChecker?**

A: Use the `--check-html` and `--check-css` options.


**Q: I want to have my own logging class. How can I use it in LinkChecker?**

A: A Python API lets you define new logging classes.
Define your own logging class as a subclass of _Logger or any other
logging class in the log module.
Then call the add_logger function in Config.Configuration to register
your new Logger.
After this append a new Logging instance to the fileoutput.

```python
import linkcheck
class MyLogger(linkcheck.logger._Logger):
    LoggerName = 'mylog'
    LoggerArgs = {'fileoutput': log_format, 'filename': 'foo.txt'}

    # ...

cfg = linkcheck.configuration.Configuration()
cfg.logger_add(MyLogger)
cfg['fileoutput'].append(cfg.logger_new(MyLogger.LoggerName)) 
```
