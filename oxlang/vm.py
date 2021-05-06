# coding: utf8

from typing import Any, Optional

from . import ast_ as ast, syntax


class Interpreter:
    def __init__(self):
        self.parser = syntax.Parser()

        # the global code namespace.
        self.context = {}

    def evaluate(self, node: ast.Node, context: Optional[dict] = None) -> Any:
        pass

    def execute(self, code: str, context: Optional[dict] = None):
        if context is None:
            # global context
            context = self.context

        body = self.parser.parse_text(code)
        for decl in body.decls:
            pass
