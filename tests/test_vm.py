# coding: utf8

import pathlib

from oxlang.runtime import Runtime

curdir = pathlib.Path(__file__).parent

rt = Runtime()

sample = """
lol = 1 + 1

struct Point {
    x, y
}

p = Point(1, 2)

x = p.x
"""


def test_sample():
    rt.execute(sample)
    print(rt.context)
    rt.reset()


def test_files():
    for file in curdir.glob("*.cub"):
        code = file.read_text()

        rt.execute(code)
        print(rt.context)
        rt.reset()
