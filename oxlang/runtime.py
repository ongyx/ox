# coding: utf8

import ast
import importlib
import pathlib

from . import syntax

STDLIB_PATH = pathlib.Path(__file__).parent / "stdlib"


class Runtime:
    def __init__(self):
        self.parser = syntax.Parser()
        # globals for the code to be executed.
        self.env = {}

        with (STDLIB_PATH / "lang.ox").open() as f:
            self.execute(f.read())

    def execute(self, code: str, filename: str = "<string>"):
        tree = ast.Module(
            body=self.parser.parse_text(code, filename=filename), type_ignores=[]
        )
        ast.fix_missing_locations(tree)

        code_obj = compile(tree, filename, mode="exec")
        exec(code_obj, self.env)

    def reset(self):
        self.env.clear()
