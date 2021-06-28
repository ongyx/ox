# coding: utf8
"""Abstract syntax tree representation of ox code."""

from __future__ import annotations

import ast
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


BINOP = {
    "+": ast.Add(),
    "-": ast.Sub(),
    "*": ast.Mult(),
    "/": ast.Div(),
    "^": ast.Pow(),
}

UNOP = {
    "-": ast.Invert(),
    "!": ast.Not(),
}

COMPARE = {
    "==": ast.Eq(),
    "!=": ast.NotEq(),
    "<": ast.Lt(),
    "<=": ast.LtE(),
    ">": ast.Gt(),
    ">=": ast.GtE(),
    "&&": ast.And(),
    "||": ast.Or(),
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
    attrs: List[str]

    def raw(self):
        return ".".join([self.name, *self.attrs])

    def compile(self):
        attrs = self.name.split(".")
        # default behaviour is to load: this can be changed by other nodes.
        var = ast.Name(id=attrs[0], ctx=ast.Load())

        for attr in attrs[1:]:
            var = ast.Attribute(value=var, attr=attr, ctx=ast.Load())

        return var


@dataclass
class Assign(Node):
    var: Variable
    value: Any  # can be a constant or a expr

    def compile(self):
        target = self.var.compile()
        target.ctx = ast.Store()

        return ast.Assign(targets=[target], value=self.value.compile())


@dataclass
class AugAssign(Assign):
    op: str

    def compile(self):
        assign = super().compile()

        return ast.AugAssign(assign.targets[0], op=BINOP[self.op], value=assign.value)


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
class Call(Node):
    # This must be set to an empty list if there are no args.
    func: Variable
    args: List[Any]

    def compile(self):
        return ast.Call(
            # the ast.Name object
            func=self.func.compile(),
            args=[a.compile() for a in self.args],
            # kwargs not supported (yet)
            keywords=[],
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
class Comparison(BinaryOp):
    def compile(self):
        return ast.Compare(
            left=self.left.compile(),
            ops=[COMPARE[self.op]],
            comparators=[self.right.compile()],
        )


@dataclass
class Body(Node):
    decls: List[Any]

    def compile(self):
        body = []

        for decl in self.decls:
            if isinstance(decl, Comment):
                # ignore comments
                continue

            elif isinstance(decl, list):
                # some decls must be made in the current scope (i.e C-style loops).
                body.extend(decl)

            else:
                # statement/expression
                node = decl.compile()

                if isinstance(node, (ast.Call, ast.Attribute, ast.Name, ast.Constant)):
                    # must be wrapped in an Expr object first.
                    node = ast.Expr(value=node)

                body.append(node)

        return body


@dataclass
class Struct(Variable):
    args: List[str]

    def compile(self):
        return ast.parse(
            textwrap.dedent(
                f"""
                {self.name} = collections.namedtuple(
                    "{self.name}",
                    "{' '.join(self.args)}"
                )
                """
            )
        ).body[0]


@dataclass
class Array(Node):
    exprs: List[Any]

    def compile(self):
        return ast.List(elts=[expr.compile() for expr in self.exprs], ctx=ast.Load())


@dataclass
class Index(Node):
    target: Any
    by: List[Any]

    def compile(self):
        subscript = None

        for index in self.by:
            subscript = ast.Subscript(
                value=subscript or self.target.compile(),
                slice=index.compile(),
                ctx=ast.Load(),
            )

        return subscript


@dataclass
class Conditional(Node):
    cond: Any
    body: Body
    # if it is a body, it is 'else'
    # if it is a conditional, it is 'else if'
    # if None, no more else ifs or elses
    orelse: Optional[Union[Conditional, Body]] = None

    def compile(self):

        if self.orelse is None:
            orelse = []
        else:
            orelse = self.orelse.compile()

        if not isinstance(orelse, list):
            # Conditionals must be wrapped in a list. Bodies are already lists.
            orelse = [orelse]

        return ast.If(test=self.cond.compile(), body=self.body.compile(), orelse=orelse)


@dataclass
class WhileLoop(Node):
    # While loop.
    cond: Any
    body: Body

    def compile(self):
        return ast.While(test=self.cond.compile(), body=self.body.compile(), orelse=[])


@dataclass
class ForLoop(Node):
    # C-style loop.
    assign: Assign
    cond: Any
    update: AugAssign
    body: Body

    def compile(self):

        # We use a while loop to emulate a C-style for loop.
        # i.e (in Cub):
        # for i = 0, i <= 10, i += 1 {
        #     print(i)
        # }
        #
        # becomes (in Python):
        #
        # i = 0
        # while i <= 10:
        #     print(i)
        #     i += 1

        body = self.body.compile()
        body.append(self.update.compile())

        return [
            self.assign.compile(),
            ast.While(test=self.cond.compile(), body=body, orelse=[]),
        ]


@dataclass
class ForInLoop(Node):
    # Iterate over a string/array.
    var: Variable
    expr: Any
    body: Body

    def compile(self):
        return ast.For(
            target=self.var.compile(),
            expr=self.expr.compile(),
            body=self.body.compile(),
            orelse=[],  # We dont support elses after loops yet.
        )


@dataclass
class Import(Node):
    module: Variable
    names: Dict[str, str]

    def compile(self):
        if self.names:
            return ast.ImportFrom(
                module=self.module.raw(),
                names=[ast.alias(name, alias) for name, alias in self.names.items()],
                level=0,
            )
        else:
            return ast.Import(names=[ast.alias(name=self.module.raw())])
