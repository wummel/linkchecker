import PyLR

class SimpleLexer(PyLR.Lexer):
    def __init__(self):
        PyLR.Lexer.__init__(self)
        self.addpat(r"c", "c")
        self.addpat(r"d", "d")
