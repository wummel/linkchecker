"""_winreg convenience wrapper (currently readonly)"""
# Copyright (C) 2001  Bastian Kleineidam (except helper functions below)
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


# import all from _winreg
from _winreg import *
from types import StringType

class key_handle:
    """represent an opened key with dictionary-like access"""
    def __init__(self, key, sub_key):
        self._key = OpenKey(key, sub_key)

    def __getitem__(self, key):
        if type(key) != StringType:
            raise TypeError, "key type must be string"
        try:
	    val = QueryValueEx(self._key, key)
        except WindowsError:
            raise IndexError, "subkey %s not found"%key
        return val[0]

    def get(self, key, default=None):
        try:
            return self[key]
        except IndexError:
            return default

    def subkeys(self):
        """get the list of subkeys as key_handle objects"""
        i = 0
        keys = []
        while 1:
            try:
                print repr(EnumKey(self._key, i))
                keys.append(key_handle(self._key, EnumKey(self._key, i)))
            except EnvironmentError:
                break
            i += 1
        return keys


    def __len__(self):
        return QueryInfoKey(self._key)[0]


    def __setitem__(self, key, value):
        """XXX to be implemented"""
        pass


    def __delitem__(self, key):
        """XXX to be implemented"""
        pass


#################################################################
# helper functions from pydns at sourceforge
# (c) 2001 Copyright by Wolfgang Strobl ws@mystrobl.de,
#          License analog to the current Python license

def binipdisplay(s):
    "convert a binary array of ip adresses to a python list"
    if len(s)%4!= 0:
        raise EnvironmentError # well ...
    ol=[]
    for i in range(len(s)/4):
        s1=s[:4]
        s=s[4:]
        ip=[]
        for j in s1:
            ip.append(str(ord(j)))
        ol.append('.'.join(ip))
    return ol

def stringdisplay(s):
    'convert "d.d.d.d,d.d.d.d" to ["d.d.d.d","d.d.d.d"]'
    return s.split(",")

#################################################################

def test():
    pass

if __name__=="__main__":
    test()
