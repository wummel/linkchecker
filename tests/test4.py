#!/usr/bin/env python

import DNS

DNS.ParseResolvConf()

print DNS.mxlookup("connect.com.au")
