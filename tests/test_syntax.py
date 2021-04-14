# coding: utf8

import pathlib

from oxlang import assignment

curdir = pathlib.Path(__file__).parent


def test_syntax():

    for file in curdir.glob("*.cub"):
        assignment.runTests(file.read_text())
