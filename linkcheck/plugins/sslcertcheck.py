# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2014 Bastian Kleineidam
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
import threading
from . import _ConnectionPlugin
from .. import log, LOG_PLUGIN, strformat, LinkCheckerError
from ..decorators import synchronized

_lock = threading.Lock()

# configuration option names
sslcertwarndays = "sslcertwarndays"

class SslCertificateCheck(_ConnectionPlugin):
    """Check SSL certificate expiration date. Only internal https: links
    will be checked. A domain will only be checked once to avoid duplicate
    warnings.
    The expiration warning time can be configured with the sslcertwarndays
    option."""

    def __init__(self, config):
        """Initialize clamav configuration."""
        super(SslCertificateCheck, self).__init__(config)
        self.warn_ssl_cert_secs_valid = config[sslcertwarndays] * strformat.SECONDS_PER_DAY
        # do not check hosts multiple times
        self.checked_hosts = set()

    @synchronized(_lock)
    def check(self, url_data):
        """Run all SSL certificate checks that have not yet been done.
        OpenSSL already checked the SSL notBefore and notAfter dates.
        """
        if url_data.extern[0]:
            # only check internal pages
            return
        if not url_data.valid:
            return
        if url_data.url_connection is None:
            # not allowed to connect
            return
        if url_data.scheme != 'https':
            return
        host = url_data.urlparts[1]
        if host in self.checked_hosts:
            return
        self.checked_hosts.add(host)
        raw_connection = url_data.url_connection.raw._connection
        if raw_connection.sock is None:
            # sometimes the socket is not yet connected
            # see https://github.com/kennethreitz/requests/issues/1966
            raw_connection.connect()
        ssl_sock = raw_connection.sock
        cert = ssl_sock.getpeercert()
        log.debug(LOG_PLUGIN, "Got SSL certificate %s", cert)
        cipher_name, ssl_protocol, secret_bits = ssl_sock.cipher()
        msg = _(u"SSL cipher %(cipher)s, %(protocol)s.")
        attrs = dict(cipher=cipher_name, protocol=ssl_protocol)
        url_data.add_info(msg % attrs)
        if 'notAfter' in cert:
            self.check_ssl_valid_date(url_data, ssl_sock, cert)
        else:
            msg = _('certificate did not include "notAfter" information')
            url_data.add_warning(msg)

    def check_ssl_valid_date(self, url_data, ssl_sock, cert):
        """Check if the certificate is still valid, or if configured check
        if it's at least a number of days valid.
        """
        import ssl
        try:
            notAfter = ssl.cert_time_to_seconds(cert['notAfter'])
        except ValueError as msg:
            msg = _('Invalid SSL certficate "notAfter" value %r') % cert['notAfter']
            url_data.add_warning(msg)
            return
        curTime = time.time()
        # Calculate seconds until certifcate expires. Can be negative if
        # the certificate is already expired.
        secondsValid = notAfter - curTime
        if secondsValid < 0:
            msg = _('SSL certficate is expired on %s') % cert['notAfter']
            url_data.add_warning(msg)
        elif secondsValid < self.warn_ssl_cert_secs_valid:
            strTimeValid = strformat.strduration_long(secondsValid)
            msg = _('SSL certificate is only %s valid') % strTimeValid
            url_data.add_warning(msg)

    @classmethod
    def read_config(cls, configparser):
        """Read configuration file options."""
        config = dict()
        section = cls.__name__
        option = sslcertwarndays
        if configparser.has_option(section, option):
            num = configparser.getint(section, option)
            if num > 0:
                config[option] = num
            else:
                msg = _("invalid value for %s: %d must not be less than %d") % (option, num, 0)
                raise LinkCheckerError(msg)
        else:
            # set the default
            config[option] = 30
        return config
