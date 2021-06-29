# coding: utf8

import ast
import pathlib

from oxlang.syntax import Lexer, Parser  # type:ignore

curdir = pathlib.Path(__file__).parent
lexer = Lexer()
parser = Parser()


def test_lexer():
    for file in curdir.glob("*.cub"):
        tokens = lexer.tokenize(file.read_text())
        tokens_list = list(tokens)
        # pprint.pp(tokens_list)
        assert len(tokens_list) > 0


def test_parser():
    for file in curdir.glob("*.cub"):

        code = file.read_text()

        print(f"* {file.name}")

        tree = parser.parse_text(code, filename=file.name)
        module = ast.Module(body=tree, type_ignores=[])
        ast.fix_missing_locations(module)

        with (curdir / f"{file.stem}.ast").open("w") as f:
            f.write(ast.dump(module, indent=4))
