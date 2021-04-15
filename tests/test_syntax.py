# coding: utf8

import pathlib

import oxlang

curdir = pathlib.Path(__file__).parent


def test_syntax():

    for file in curdir.glob("*.cub"):
        tree = oxlang.Parser.searchString(file.read_text())
        print(tree.dump())
        assert len(tree) > 0
