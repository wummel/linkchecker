# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2014 Bastian Kleineidam
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
Test mail checking of bad mail addresses.
"""
from . import MailTest


class TestMailBad (MailTest):
    """Test mailto: link checking."""

    def test_error_mail (self):
        # too long or too short
        self.mail_error(u"mailto:@")
        self.mail_error(u"mailto:@example.org")
        self.mail_error(u"mailto:a@")
        self.mail_error(u"mailto:%s@example.org" % (u"a"*65))
        self.mail_error(u'mailto:a@%s.com' % (u"a"*64))
        # local part quoted
        self.mail_error(u'mailto:"a""@example.com', cache_key=u'mailto:a')
        self.mail_error(u'mailto:""a"@example.com', cache_key=u'mailto:""a"@example.com')
        self.mail_error(u'mailto:"a\\"@example.com', cache_key=u'mailto:a"@example.com')
        # local part unqouted
        self.mail_error(u'mailto:.a@example.com')
        self.mail_error(u'mailto:a.@example.com')
        self.mail_error(u'mailto:a..b@example.com')
        # domain part
        self.mail_error(u'mailto:a@a_b.com')
        self.mail_error(u'mailto:a@example.com.')
        self.mail_error(u'mailto:a@example.com.111')
        self.mail_error(u'mailto:a@example..com')
        # other
        # ? extension forbidden in <> construct
        self.mail_error(u"mailto:Bastian Kleineidam <calvin@users.sourceforge.net?foo=bar>",
            cache_key=u"mailto:calvin@users.sourceforge.net?foo=bar")
