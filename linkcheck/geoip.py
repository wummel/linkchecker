# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2010 Bastian Kleineidam
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
Store and retrieve country names for IPs.
"""
import os
import sys
from ..lock import get_lock
from ..decorators import synchronized
from ..strformat import unicode_safe

# It is unknown if the geoip library is already thread-safe, so
# no risks should be taken here by using a lock.
_lock = get_lock("geoip")

def get_geoip_dat ():
    """Find a GeoIP database, preferring city over country lookup."""
    datafiles = ("GeoIPCity.dat", "GeoIP.dat")
    if os.name == 'nt':
        paths = (sys.exec_prefix, r"c:\geoip")
    else:
        paths = ("/usr/local/share/GeoIP", "/usr/share/GeoIP")
    for path in paths:
        for datafile in datafiles:
            filename = os.path.join(path, datafile)
            if os.path.exists(filename):
                return filename

# try importing both the C-library GeoIP and the pure-python pygeoip
geoip_dat = get_geoip_dat()
geoip = None
if geoip_dat:
    try:
        import GeoIP
        geoip = GeoIP.open(geoip_dat, GeoIP.GEOIP_STANDARD)
        geoip_error = GeoIP.error
    except ImportError:
        try:
            import pygeoip
            geoip = pygeoip.GeoIP(geoip_dat)
            geoip_error = pygeoip.GeoIPError
        except ImportError:
            pass


@synchronized(_lock)
def get_country (host):
    """Get translated country name.

    @return: country with optional city or an boolean False if not found
    """
    if geoip is None:
        # no geoip available
        return None
    try:
        record = geoip.record_by_name(host)
    except geoip_error:
        # ignore lookup errors
        return None
    value = u""
    if record and record.get("city"):
        value += unicode_safe(record["city"])
    if record and record.get("country_name"):
        if value:
            value += u", "
        value += unicode_safe(record["country_name"])
    return value
