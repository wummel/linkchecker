from SimpleParser import SimpleParser

class mysimpleparser(SimpleParser):
    pass


def _test():
    p = mysimpleparser()
    p.pyparse("c",1)


if __name__=='__main__':
    _test()
