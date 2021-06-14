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
p.x = 9
"""


def test_sample():
    rt.execute(sample)
    print(rt.context)
    rt.reset()


def test_files():
    for file in curdir.glob("*.cub"):
        print(f"* {file.name}")
        if file.name == "example.cub":
            continue

        code = file.read_text()

        try:
            rt.execute(code)
        except RecursionError:
            print(f"code too complex (probably recursion): {file}")
        except RuntimeError:
            print(code)
            raise

        rt.reset()
