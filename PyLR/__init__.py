"""
This package has the following modules and characteristics: 

(-) = not done yet
(*) = done
(?) = working on it

PyLR/    				the top level module Language Genration Tools
    __init__.py(*)			this file
    Lexer.py(*) 			defines the Lexer interface that the parser will use, uses re
    Lexers/(?)                          a package to put lexers for different things
           __init__                     imports GrammarLex class
           GrammarLex.py                The module that defines the lexer for grammar specifications
    Grammar.py(*)                       The module for dealing with grammars
    PyLRenginemodule.so(*)              The engine behind a LR parser (can do SLR, LR, and LALR)
    Parser.py (*)                       A class interface to a parser
    Parsers/(?)                         A package for storing Parsers
            __init__                    imports GrammarParser class                   
            gram.py(*)                  the definition of the GrammarParser (import into Parsers/ namespace)
    pgen.py(*)                          a script for parser generation
    parsertemplate.py                   the doc string of this module is the template for parser generation


"""


from Lexer import Lexer
import Parser,Lexers,Parsers


__version__ = "$Id$"








