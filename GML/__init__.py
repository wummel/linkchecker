
from GMLLexer import GMLLexer
from GMLBaseParser import GMLBaseParser
import types

class GMLParser(GMLBaseParser):
    def __init__(self):
	GMLBaseParser.__init__(self)
	self.result = []

    def key_value(self, key, value):
        return [(key,value)]

    def gml_key_value(self, gml, key_value):
        return gml + key_value

    def gmllist(self, lsqb, gml, rsqb):
        return gml

    def feddich(self, l):
        self.result = l

    def __repr__(self):
        return self.getRepr(self.result, 0)

    def getRepr(self, lst, indent=0):
        indentStr = " "*indent
        res = indentStr
        lenlst = len(lst)
        i=0
        for i in range(lenlst):
            item = lst[i]
            res = res+item[0]+" "
            if type(item[1])==types.ListType:
                res = res+"[\n"+self.getRepr(item[1], indent+2)+"\n"+indentStr+"]"
            elif type(item[1])==types.StringType:
                res = res +'"'+item[1]+'"'
            else:
                res = res+`item[1]`
            if i != lenlst-1:
                res = res+"\n"+indentStr
        return res

def _test():
    p =GMLParser()
    text = """AINS 1
    graph [
       innen 1
       innen 2
    ]
    ZWAI 2
    """
    p.parse(text, 1)
    print p

if __name__=='__main__':
    _test()