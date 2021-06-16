# coding: utf8
"""Abstract syntax tree representation of ox code."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, List, Optional, Union


BINOP = {
    "+": ast.Add,
    "-": ast.Sub,
    "*": ast.Mult,
    "/": ast.Div,
    "^": ast.Pow,
    "==": ast.Eq,
    "!=": ast.NotEq,
    "<": ast.Lt,
    "<=": ast.LtE,
    ">": ast.Gt,
    ">=": ast.GtE,
    "&&": ast.And,
    "||": ast.Or,
}

UNOP = {
    "-": ast.Invert,
    "!": ast.Not,
}


@dataclass
class Node:
    lineno: int
    index: int

    def compile(self) -> Optional[ast.AST]:
        pass


@dataclass
class Comment(Node):
    text: str

    def compile(self):
        return


@dataclass
class Constant(Node):
    # A hardcoded value in the code.
    value: Any

    def compile(self):
        return ast.Constant(value=self.value)


@dataclass
class Variable(Node):
    # A variable in the current or global namespace.
    name: str

    def compile(self):
        # default behaviour is to load: this can be changed by other nodes.
        return ast.Variable(id=self.name, ctx=ast.Load())


@dataclass
class Assign(Node):
    var: Variable
    value: Any  # can be a constant or a expr

    def compile(self):
        target = self.var.compile()
        target.ctx = ast.Store()

        return ast.Assign(targets=[target], value=self.value.compile())


@dataclass
class Function(Variable):
    args: List[str]
    body: Body

    def compile(self):
        return ast.FunctionDef(
            name=self.name,
            args=[ast.arg(a) for a in self.args],
            body=self.body.compile(),
        )


@dataclass
class Call(Variable):
    # This must be set to an empty list if there are no args.
    args: List[Any]

    def compile(self):
        return ast.Call(
            # the ast.Name object
            func=super().compile(),
            args=[a.compile() for a in self.args],
        )


@dataclass
class FunctionReturn(Node):
    expr: Any

    def compile(self):
        return ast.Return(value=self.expr.compile())


@dataclass
class UnaryOp(Node):
    op: str
    right: Any  # if the type is Any, it is an expression.

    def compile(self):
        return ast.UnaryOp(op=UNOP[self.op], operand=self.right.compile())


@dataclass
class BinaryOp(Node):
    op: str
    left: Any
    right: Any

    def compile(self):
        return ast.BinOp(
            left=self.left.compile(), op=BINOP[self.op], right=self.right.compile()
        )


@dataclass
class Body(Node):
    decls: List[Any]

    def compile(self):
        return [decl.compile() for decl in self.decls if not isinstance(decl, Comment)]


@dataclass
class Struct(Variable):
    args: List[str]
    inherits: List[str]


@dataclass
class Array(Node):
    exprs: List[Any]


@dataclass
class Index(Node):
    target: Any
    by: List[Any]


@dataclass
class Conditional(Node):
    cond: Any
    body: Body
    # if it is a body, it is 'else'
    # if it is a conditional, it is 'else if'
    # if None, no more else ifs or elses
    orelse: Optional[Union[Conditional, Body]] = None


@dataclass
class Loop(Node):
    cond: Any
    body: Body
    # preloop is executed once in the loop's context.
    # postloop is executed for every iteration in the loop's context.
    preloop: Optional[Assign] = None
    postloop: Optional[Assign] = None


@dataclass
class ForInLoop(Node):
    # A special case of 'for' to iterate over a string/array.
    var: Variable
    expr: Any
    body: Body


@dataclass
class Import(Node):
    module: str
