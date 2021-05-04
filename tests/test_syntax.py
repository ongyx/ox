# coding: utf8

import dataclasses
import json
import pprint

import pathlib

import oxlang.syntax

curdir = pathlib.Path(__file__).parent
lexer = oxlang.syntax.Lexer()
parser = oxlang.syntax.Parser()


def test_lexer():
    for file in curdir.glob("*.cub"):
        tokens = lexer.tokenize(file.read_text())
        tokens_list = list(tokens)
        # pprint.pp(tokens_list)
        assert len(tokens_list) > 0


def test_parser():
    for file in curdir.glob("*.cub"):

        tokens = lexer.tokenize(file.read_text())

        print(file.name)

        tree = parser.parse(tokens)

        # print(json.dumps(dataclasses.asdict(tree), indent=2))

        assert tree.decls
