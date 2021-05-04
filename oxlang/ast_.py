# coding: utf8
"""Abstract syntax tree representation of ox code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Literal, Optional, Union


@dataclass
class Variable:
    # The variable is a literal if value is not None.
    # Otherwise, the name is a reference to a variable in the current/global context.
    # If both are set, name is given priority (should be impossible)
    name: Optional[str]
    value: Any = None
    op: Literal["get", "set", "delete"] = "get"


class FunctionCall(Variable):
    pass


@dataclass
class BinaryOp:
    op: str
    left: Union[BinaryOp, Variable]
    right: Union[BinaryOp, Variable]


@dataclass
class Body:
    decls: List[Any]


@dataclass
class Function:
    name: str
    args: List[str]
    body: Body


@dataclass
class FunctionReturn:
    expr: Any


@dataclass
class Struct:
    name: str
    args: List[str]


@dataclass
class Array:
    exprs: List[Any]


@dataclass
class Conditional:
    name: str
    cond: Optional[Union[BinaryOp, Variable]]
    body: Body


@dataclass
class Loop:
    cond: Union[BinaryOp, Variable]
    body: Body
    # The for loop requires these two variables. Both must have context 'set'.
    # preloop is executed once in the loop's parent context.
    # postloop is executed for every loop iteration in the loop's context.
    preloop: Optional[Variable] = None
    postloop: Optional[Variable] = None
