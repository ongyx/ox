# coding: utf8

import pathlib

import oxlang.syntax

curdir = pathlib.Path(__file__).parent


def test_syntax():

    lexer = oxlang.syntax.Lexer()

    for file in curdir.glob("*.cub"):
        tree = list(lexer.tokenize(file.read_text()))
        # print(tree)
        assert len(tree) > 0
