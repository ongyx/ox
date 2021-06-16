# coding: utf8

import enum
import functools
import operator
import pathlib
from typing import Callable, List, Optional

from . import ast_ as ast, syntax

STDLIB_PATH = pathlib.Path(__file__).parent / "stdlib"


BINOP_MAP = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "truediv",
    "^": "pow",
    "==": "eq",
    "!=": "ne",
    "<": "lt",
    "<=": "le",
    ">": "gt",
    ">=": "ge",
    "&&": "and_",
    "||": "or_",
}

UNOP_MAP = {
    "-": "neg",
    "!": "not_",
}


def _deep_get(d, ks):
    v = d
    for k in ks:
        v = v[k]

    return v


def _deep_set(d, ks, v):
    for k in ks[:-1]:
        d = d[k]

    d[ks[-1]] = v


class BodyResult(enum.Enum):
    CONTINUE = 1
    BREAK = 2
    ERROR = 3


class Runtime:
    def __init__(self):
        self.parser = syntax.Parser()

        # the global context (namespace).
        self.context = {}
        self.reset()

        self.lib_paths = [STDLIB_PATH]

        self.code = []

    def register(
        self, name: str, args: List[str], func: Callable, context: Optional[dict] = None
    ):
        """Register a native Python function in the runtime.
        The function should only return one of ox's basic types.

        Args:
            name: The function name.
            args: A list of argument names of the function.
                If it is a varadic function (i.e has *args in its signature), the last arg should end with "..." (an ellipsis).
            func: The native Python function.
            context: The context to register the function in.
                Defaults to None (global context).
        """

        if context is None:
            context = self.context

        wrapper = ast.Function(0, 0, name=name, args=args, body=func)  # type: ignore

        context[name] = wrapper

    def reset(self):
        """Reset the runtime's context."""
        self.context = self._new_context()

    def _new_context(self):
        context = {}

        self.register("print", ["values..."], functools.partial(print, end=""), context)
        self.register("println", ["values..."], print, context)

        return context

    def execute(
        self, code: str, context: Optional[dict] = None, _library: bool = False
    ):
        """Execute code in the runtime.

        Args:
            code: The ox code to execute.
            context: The context to execute the code in.
                Defaults to None (global context).
        """
        if context is None:
            # global context
            context = self.context

        self.code = code.splitlines()

        try:
            body = self.parser.parse_text(code)
            self.visit(body, context)
        except Exception:
            raise

    def _index(self, lineno, index):
        lines = self.code[:lineno]
        total = sum(len(line) for line in lines)

        return index - total - len(lines)

    def error(self, node: ast.Node, msg: str = "Runtime error"):

        # line numbers are always zero-indexed.
        lineno = node.lineno - 1
        index = self._index(lineno, node.index)

        code_line = self.code[lineno]

        raise RuntimeError(
            syntax.ERROR_TEMPLATE.format(  # type: ignore
                filename=self.parser.filename,
                context="<runtime>",
                line=lineno,
                pos=index,
                message=msg,
                code=code_line,
                indent=" " * index,
                arrows="^" * (len(code_line) - index),
            )
        )

    def visit(self, node: ast.Node, context: dict):
        visitor = getattr(self, f"visit_{node.__class__.__name__}", self.visit_generic)

        return visitor(node, context)

    def visit_generic(self, node, context):
        print(f"unimplemented visit for node {node}")

    def visit_Import(self, node, context):
        if node.module.startswith("pragma"):
            return

        code = None

        for path in self.lib_paths:
            try:
                code = (path / f"{node.module}.ox").read_text()
            except FileNotFoundError:
                pass

        if code is None:
            self.error(node, f"library not found: {node.module}")

        self.execute(code, _library=True)

    def visit_Comment(self, node, context):
        pass

    def visit_Constant(self, node, context):
        return node.value

    def visit_Variable(self, node, context):
        name = node.name.split(".")
        for ctx in (context, self.context):
            try:
                return _deep_get(ctx, name)
            except (KeyError, TypeError):
                pass

        self.error(node, f"undefined variable: {node.name}")

    def visit_Assign(self, node, context):
        _deep_set(context, node.var.name.split("."), self.visit(node.value, context))

    def visit_Function(self, node, context):
        context[node.name] = node

    def visit_Call(self, node, context):

        func = self.visit_Variable(node, context)

        if not isinstance(func, (ast.Function, ast.Struct)):
            self.error(node, f"can't call {node.name}: not a function or struct")

        expected = len(func.args)
        got = len(node.args)

        if not func.args[-1].endswith("...") and expected != got:
            # not a varadic function
            self.error(
                node,
                f"function or struct {func.name} expected {expected} args, got {got}",
            )

        args = [self.visit(arg, context) for arg in node.args]

        # construct a new context for the function/struct.
        new_context = {}
        for count, (name, arg) in enumerate(zip(func.args, args)):
            if name.endswith("..."):
                # add varargs as an array
                new_context[name] = args[count:]
                break
            else:
                new_context[name] = arg

        if isinstance(func, ast.Function):
            if not isinstance(func.body, ast.Body):
                # native function, call it instead.
                return func.body(*args)

            return self.visit_Body(func.body, new_context)
        else:
            return new_context

    def visit_FunctionReturn(self, node, context):
        return self.visit(node.expr, context)

    def visit_UnaryOp(self, node, context):
        value = self.visit(node.right, context)

        dunder = getattr(operator, UNOP_MAP[node.op])
        return dunder(value)

    def visit_BinaryOp(self, node, context):
        left_value = self.visit(node.left, context)
        right_value = self.visit(node.right, context)

        dunder = getattr(operator, BINOP_MAP[node.op])
        return dunder(left_value, right_value)

    def visit_Body(self, node, context):
        for decl in node.decls:

            if decl == "continue":
                return BodyResult.CONTINUE
            elif decl == "break":
                return BodyResult.BREAK

            value = self.visit(decl, context)
            if isinstance(decl, ast.FunctionReturn):
                return value

    def visit_Struct(self, node, context):
        context[node.name] = node

    def visit_Array(self, node, context):
        return [self.visit(item, context) for item in node.exprs]

    def visit_Index(self, node, context):
        target = self.visit(node.target, context)
        by = [self.visit(index, context) for index in node.by]

        return _deep_get(target, by)

    def visit_Conditional(self, node, context):
        if self.visit(node.cond, context):
            self.visit_Body(node.body, context)

        else:
            if node.orelse is not None:
                self.visit(node.orelse, context)

    def visit_Loop(self, node, context):
        # Like Python, loop variables are not local.
        # They use the parent context.

        if node.preloop is not None:
            self.visit_Assign(node.preloop, context)

        while True:
            if self.visit(node.cond, context):
                result = self.visit_Body(node.body, context)
                if result == BodyResult.BREAK:
                    break
            else:
                break

            if node.postloop is not None:
                self.visit_Assign(node.postloop, context)

    def visit_ForInLoop(self, node, context):
        expr = self.visit(node.expr, context)

        if not isinstance(expr, (str, list)):
            self.error(node, "can't iterate: not a string or list")

        for item in expr:
            context[node.var.name] = item
            self.visit_Body(node.body, context)
