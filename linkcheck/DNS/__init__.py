# -*- coding: iso-8859-1 -*-
# $Id$
#
# This file is part of the pydns project.
# Homepage: http://pydns.sourceforge.net
#
# This code is covered by the standard Python License.
#

# __init__.py for DNS class.

__version__ = '2.3.0'

import Base
import Lib

Error = Base.DNSError
Request = Base.DnsRequest
Result = Lib.DnsResult

Base.DiscoverNameServers()
