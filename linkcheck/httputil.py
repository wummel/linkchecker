# -*- coding: iso-8859-1 -*-
# Various HTTP utils with a free license
from cStringIO import StringIO
from . import gzip2 as gzip
from . import httplib2 as httplib
from . import log, LOG_CHECK, fileutil
import re
import zlib
import urllib
import urllib2
import base64


###########################################################################
# urlutils.py - Simplified urllib handling
#
#   Written by Chris Lawrence <lawrencc@debian.org>
#   (C) 1999-2002 Chris Lawrence
#
# This program is freely distributable per the following license:
#
##  Permission to use, copy, modify, and distribute this software and its
##  documentation for any purpose and without fee is hereby granted,
##  provided that the above copyright notice appears in all copies and that
##  both that copyright notice and this permission notice appear in
##  supporting documentation.
##
##  I DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
##  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL I
##  BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
##  DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
##  WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
##  ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
##  SOFTWARE.

def decode (page):
    """Gunzip or deflate a compressed page."""
    log.debug(LOG_CHECK, "page info %d %s", page.code, str(page.info()))
    encoding = page.info().get("Content-Encoding")
    if encoding in ('gzip', 'x-gzip', 'deflate'):
        # cannot seek in socket descriptors, so must get content now
        content = page.read()
        try:
            if encoding == 'deflate':
                fp = StringIO(zlib.decompress(content))
            else:
                fp = gzip.GzipFile('', 'rb', 9, StringIO(content))
        except zlib.error as msg:
            log.debug(LOG_CHECK, "uncompressing had error "
                 "%s, assuming non-compressed content", str(msg))
            fp = StringIO(content)
        # remove content-encoding header
        headers = httplib.HTTPMessage(StringIO(""))
        ceheader = re.compile(r"(?i)content-encoding:")
        for h in page.info().keys():
            if not ceheader.match(h):
                headers[h] = page.info()[h]
        newpage = urllib.addinfourl(fp, headers, page.geturl())
        newpage.code = page.code
        newpage.msg = page.msg
        return newpage
    return page


class HttpWithGzipHandler (urllib2.HTTPHandler):
    """Support gzip encoding."""
    def http_open (self, req):
        """Send request and decode answer."""
        return decode(urllib2.HTTPHandler.http_open(self, req))


if hasattr(httplib, 'HTTPS'):
    class HttpsWithGzipHandler (urllib2.HTTPSHandler):
        """Support gzip encoding."""

        def https_open (self, req):
            """Send request and decode answer."""
            return decode(urllib2.HTTPSHandler.https_open(self, req))

# end of urlutils.py routines
###########################################################################


def encode_multipart_formdata(fields, files=None):
    """
    From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306

    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    if files is not None:
        for (key, filename, value) in files:
            content_type = fileutil.guess_mimetype(filename)
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % content_type)
            L.append('')
            L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def encode_base64 (s):
    """Encode given string in base64, excluding trailing newlines."""
    return base64.b64encode(s)
