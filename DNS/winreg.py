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

    def __len__(self):
        return QueryInfoKey(self._key)[0]

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass


def test():
    pass

if __name__=="__main__":
    test()
