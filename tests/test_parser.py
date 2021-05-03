# coding: utf8

from oxlang.syntax import Lexer, Parser


sample = """
lol()
"""


def test_lexer():
    lexer = Lexer()
    parser = Parser()

    tokens = list(lexer.tokenize(sample))
    print(tokens)

    tree = parser.parse(iter(tokens))
    print(tree)
