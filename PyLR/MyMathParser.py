import PyLR

class MyMathParser(PyLR.Parsers.MathParser):
    def addfunc(self, left, plus, right):
        print "%d + %d" % (left, right)
        return left + right
    def parenfunc(self, lp, expr, rp):
        print "handling parens"
        return expr
    def timesfunc(self, left, times, right):
        print "%d * %d" % (left, right)
        return left * right

def _test():
    p = MyMathParser()
    p.parse("4 * (3 + 2 * 5)", 1)

if __name__=='__main__':
    _test()