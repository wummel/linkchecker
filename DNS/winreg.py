"""Bastis winreg module to wrap the inconvenient _winreg module"""

# import all from _winreg
from _winreg import *
from types import StringType

class key_handle:
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
        i = 0
        keys = []
        while 1:
            try:
                keys.append(OpenKey(self._key, EnumKey(self._key, i)))
            except EnvironmentError:
                break
        return keys

    def __len__(self):
        return QueryInfoKey(self._key)[0]

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass


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
