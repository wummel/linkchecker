#!/usr/bin/python
"""
    Copyright (C) 2000  Bastian Kleineidam

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

# profiling test
import sys, profile, os
sys.path.append(os.getcwd())
import linkcheck

#linkcheck.Config.DebugFlag = 1

def runit (config, name):
    url='http://www.heise.de/'
    config['recursionlevel'] = 1
    config['anchors'] = 1
    config['internlinks'].append(linkcheck.getLinkPat(r"^https?://www\.heise\.de"))
    # avoid checking of local files (security!)
    config["externlinks"].append(linkcheck.getLinkPat("^file:", strict=1))
    config.appendUrl(linkcheck.UrlData.GetUrlDataFrom(url, 0, config))
    profile.run("linkcheck.checkUrls(config)", name)

if __name__=='__main__':
    config = linkcheck.Config.Configuration()
    config.disableThreading()
    runit(config, "nothreads.prof")
    config.reset()
    config.enableThreading(10)
    runit(config, "threads.prof")

