# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2012 Bastian Kleineidam
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
Handle https links.
"""
import time
from . import httpurl
from .const import WARN_HTTPS_CERTIFICATE
from .. import log, LOG_CHECK, strformat


class HttpsUrl (httpurl.HttpUrl):
    """
    Url link with https scheme.
    """

    def local_check (self):
        """
        Check connection if SSL is supported, else ignore.
        """
        if httpurl.supportHttps:
            super(HttpsUrl, self).local_check()
        else:
            self.add_info(_("%s URL ignored.") % self.scheme.capitalize())

    def get_http_object (self, host, scheme):
        """Open a HTTP connection and check the SSL certificate."""
        h = super(HttpsUrl, self).get_http_object(host, scheme)
        self.check_ssl_certificate(h.sock, host)
        return h

    def check_ssl_certificate(self, ssl_sock, host):
        """Run all SSl certificate checks that have not yet been done.
        OpenSSL already checked the SSL notBefore and notAfter dates.
        """
        cert = ssl_sock.getpeercert()
        log.debug(LOG_CHECK, "Got SSL certificate %s", cert)
        if not cert:
            msg = _('empty or no certificate found')
            self.add_ssl_warning(ssl_sock, msg)
            return
        if 'subject' in cert:
            self.check_ssl_hostname(ssl_sock, cert, host)
        else:
            msg = _('certificate did not include "subject" information')
            self.add_ssl_warning(ssl_sock, msg)
        if 'notAfter' in cert:
            self.check_ssl_valid_date(ssl_sock, cert)
        else:
            msg = _('certificate did not include "notAfter" information')
            self.add_ssl_warning(ssl_sock, msg)

    def check_ssl_hostname(self, ssl_sock, cert, host):
        """Check the hostname against the certificate according to
        RFC2818.
        """
        try:
            match_hostname(cert, host)
        except CertificateError, msg:
            self.add_ssl_warning(ssl_sock, msg)

    def check_ssl_valid_date(self, ssl_sock, cert):
        """Check if the certificate is still valid, or if configured check
        if it's at least a number of days valid.
        """
        import ssl
        checkDaysValid = self.aggregate.config["warnsslcertdaysvalid"]
        try:
            notAfter = ssl.cert_time_to_seconds(cert['notAfter'])
        except ValueError, msg:
            msg = _('invalid certficate "notAfter" value %r') % cert['notAfter']
            self.add_ssl_warning(ssl_sock, msg)
            return
        curTime = time.time()
        # Calculate seconds until certifcate expires. Can be negative if
        # the certificate is already expired.
        secondsValid = notAfter - curTime
        if secondsValid < 0:
            msg = _('certficate is expired on %s') % cert['notAfter']
            self.add_ssl_warning(ssl_sock, msg)
        elif checkDaysValid > 0 and \
              secondsValid < (checkDaysValid * strformat.SECONDS_PER_DAY):
            strSecondsValid = strformat.str_duration_long(secondsValid)
            msg = _('certificate is only %s valid') % strSecondsValid
            self.add_ssl_warning(ssl_sock, msg)

    def add_ssl_warning(self, ssl_sock, msg):
        """Add a warning message about an SSL certificate error."""
        cipher_name, ssl_protocol, secret_bits = ssl_sock.cipher()
        err = _(u"SSL warning: %(msg)s. Cipher %(cipher)s, %(protocol)s.")
        attrs = dict(msg=msg, cipher=cipher_name, protocol=ssl_protocol)
        self.add_warning(err % attrs, tag=WARN_HTTPS_CERTIFICATE)


# Copied from ssl.py in Python 3:
# Wrapper module for _ssl, providing some additional facilities
# implemented in Python.  Written by Bill Janssen.
import re

class CertificateError(ValueError):
    """Raised on certificate errors."""
    pass


def _dnsname_to_pat(dn):
    """Convert a DNS certificate name to a hostname matcher."""
    pats = []
    for frag in dn.split(r'.'):
        if frag == '*':
            # When '*' is a fragment by itself, it matches a non-empty dotless
            # fragment.
            pats.append('[^.]+')
        else:
            # Otherwise, '*' matches any dotless fragment.
            frag = re.escape(frag)
            pats.append(frag.replace(r'\*', '[^.]*'))
    return re.compile(r'\A' + r'\.'.join(pats) + r'\Z', re.IGNORECASE)


def match_hostname(cert, hostname):
    """Verify that *cert* (in decoded format as returned by
    SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 rules
    are mostly followed, but IP addresses are not accepted for *hostname*.

    CertificateError is raised on failure. On success, the function
    returns nothing.
    """
    if not cert:
        raise ValueError("empty or no certificate")
    dnsnames = []
    san = cert.get('subjectAltName', ())
    for key, value in san:
        if key == 'DNS':
            if _dnsname_to_pat(value).match(hostname):
                return
            dnsnames.append(value)
    if not dnsnames:
        # The subject is only checked when there is no dNSName entry
        # in subjectAltName
        for sub in cert.get('subject', ()):
            for key, value in sub:
                # XXX according to RFC 2818, the most specific Common Name
                # must be used.
                if key == 'commonName':
                    if _dnsname_to_pat(value).match(hostname):
                        return
                    dnsnames.append(value)
    if len(dnsnames) > 1:
        raise CertificateError("hostname %r "
            "doesn't match either of %s"
            % (hostname, ', '.join(map(repr, dnsnames))))
    elif len(dnsnames) == 1:
        raise CertificateError("hostname %r "
            "doesn't match %r"
            % (hostname, dnsnames[0]))
    else:
        raise CertificateError("no appropriate commonName or "
            "subjectAltName fields were found")
