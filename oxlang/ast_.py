# coding: utf8
"""Abstract syntax tree representation of ox code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Union


class Node:
    pass


@dataclass
class Comment(Node):
    text: str


@dataclass
class Constant(Node):
    # A hardcoded value in the code.
    value: Any


@dataclass
class Variable(Node):
    # A variable in the current or global namespace.
    name: str


@dataclass
class Assign(Node):
    var: Variable
    value: Any  # can be a constant or a expr


@dataclass
class Function(Variable):
    args: List[str]
    body: Body


@dataclass
class FunctionCall(Variable):
    # This must be set to an empty list if there are no args.
    args: List[Any]


@dataclass
class FunctionReturn(Node):
    expr: Any


@dataclass
class UnaryOp(Node):
    op: str
    right: Any  # if the type is Any, it is an expression.


@dataclass
class BinaryOp(Node):
    op: str
    left: Any
    right: Any


@dataclass
class Body(Node):
    decls: List[Any]


@dataclass
class Struct(Variable):
    args: List[str]
    inherits: List[str]


@dataclass
class Array(Node):
    exprs: List[Any]


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
    preloop: Optional[Variable] = None
    postloop: Optional[Variable] = None


@dataclass
class Import(Node):
    module: str
