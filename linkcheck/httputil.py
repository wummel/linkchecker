# -*- coding: iso-8859-1 -*-
# Various HTTP utils with a free license
from . import fileutil
import base64


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
