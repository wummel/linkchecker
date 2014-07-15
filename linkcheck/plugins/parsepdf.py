# -*- coding: iso-8859-1 -*-
# Copyright (C) 2014 Bastian Kleineidam
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
Parse links in PDF files with pdfminer.
"""
from cStringIO import StringIO
from . import _ParserPlugin
try:
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdftypes import PDFStream, PDFObjRef
    from pdfminer.pdfpage import PDFPage
    from pdfminer.psparser import PSException
except ImportError:
    has_pdflib = False
else:
    has_pdflib = True
from .. import log, LOG_PLUGIN, strformat



def search_url(obj, url_data, pageno, seen_objs):
    """Recurse through a PDF object, searching for URLs."""
    if isinstance(obj, PDFObjRef):
        if obj.objid in seen_objs:
            # prevent recursive loops
            return
        seen_objs.add(obj.objid)
        obj = obj.resolve()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'URI' and isinstance(value, basestring):
                # URIs should be 7bit ASCII encoded, but be safe and encode
                # to unicode
                # XXX this does not use an optional specified base URL
                url = strformat.unicode_safe(value)
                url_data.add_url(url, page=pageno)
            else:
                search_url(value, url_data, pageno, seen_objs)
    elif isinstance(obj, list):
        for elem in obj:
            search_url(elem, url_data, pageno, seen_objs)
    elif isinstance(obj, PDFStream):
        search_url(obj.attrs, url_data, pageno, seen_objs)


class PdfParser(_ParserPlugin):
    """PDF parsing plugin."""

    def __init__(self, config):
        """Check for pdfminer."""
        if not has_pdflib:
            log.warn(LOG_PLUGIN, "pdfminer not found for PdfParser plugin")
        super(PdfParser, self).__init__(config)

    def applies_to(self, url_data, pagetype=None):
        """Check for PDF pagetype."""
        return has_pdflib and pagetype == 'pdf'

    def check(self, url_data):
        """Parse PDF data."""
        # XXX user authentication from url_data
        password = ''
        data = url_data.get_content()
        # PDFParser needs a seekable file object
        fp = StringIO(data)
        try:
            parser = PDFParser(fp)
            doc = PDFDocument(parser, password=password)
            for (pageno, page) in enumerate(PDFPage.create_pages(doc), start=1):
                if "Contents" in page.attrs:
                    search_url(page.attrs["Contents"], url_data, pageno, set())
                if "Annots" in page.attrs:
                    search_url(page.attrs["Annots"], url_data, pageno, set())
        except PSException as msg:
            if not msg.args:
                # at least show the class name
                msg = repr(msg)
            log.warn(LOG_PLUGIN, "Error parsing PDF file: %s", msg)
