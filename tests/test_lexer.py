# coding: utf8

import pathlib

import oxlang.syntax

curdir = pathlib.Path(__file__).parent


def test_lexer():

    lexer = oxlang.syntax.Lexer()

    for file in curdir.glob("*.cub"):
        tokens = lexer.tokenize(file.read_text())
        tokens_list = list(tokens)
        assert len(tokens_list) > 0
