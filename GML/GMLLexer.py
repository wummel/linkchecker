import sys,re
import PyLR

def _intfunc(m):
    return int(m.group(0))

def _realfunc(m):
    return float(m.group(0))

class GMLLexer(PyLR.Lexer):
    """The GML lexical scanner."""
    def __init__(self):
        PyLR.Lexer.__init__(self)
        self.addpat(r"[-+]?(\d+\.\d*|\d*\.\d+)([Ee][-+]?\d+)?",
	              "REAL", _realfunc)
        self.addpat(r"[-+]?\d+", "INT", _intfunc)
        self.addpat(r"\[", "LSQB")
        self.addpat(r"\]", "RSQB")
        self.addpat(r'"([^&"]+|&[a-zA-Z]+;)*"', "STRING")
        self.addpat(r"[a-zA-Z][a-zA-Z0-9]*", "KEY")
        self.addpat(r"#[^\n]*", "", None, 1)
        self.addpat(r"\s+", "", None, 1)

def _test():
    gmltest = """# a graph example
    graph [ # comment at end of line
      node [
        real1 1.e3
        real2 .01
        int1 00050
        label "Wallerfang&amp;Ballern"
      ]
    ]
    """
    # create the lexer
    lexer = GMLLexer()
    lexer.settext(gmltest)
    print lexer.getTokenList()
    tok=1
    while tok:
        tok, val = lexer.scan(1)

if __name__ == '__main__':
    _test()
