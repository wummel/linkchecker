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
import Template,os

distpath = os.getcwd()
t = Template.Template("linkcheck/__init__.py.tmpl")
f = open("linkcheck/__init__.py","w")
f.write(t.fill_in({"install_data": distpath}))
f.close()
for name in ['linkchecker','test/profiletest.py']:
    t = Template.Template(name+".tmpl")
    f = open(name,"w")
    f.write(t.fill_in({"syspath": "sys.path.insert(0, '"+distpath+"')"}))
    f.close()
os.chmod("linkchecker", 0755)
t = Template.Template("linkchecker.bat.tmpl")
f = open("linkchecker.bat","w")
f.write(t.fill_in({"install_scripts": distpath}))
f.close()
print "Local installation ok"
