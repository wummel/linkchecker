from SimpleParser import SimpleParser

class mysimpleparser(SimpleParser):
    pass


def _test():
    p = mysimpleparser()
    p.parse("dd",1)


if __name__=='__main__':
    _test()
