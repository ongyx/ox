# coding: utf8
# type: ignore
# flake8: noqa
"""ox's core syntax lexer and parser."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

import sly


class Lexer(sly.Lexer):

    ignore = " \t\n"
    ignore_comment = r"//.*"

    tokens = {
        ID,
        NUMBER,
        STRING,
        TRUE,
        FALSE,
        NIL,
        IF,
        ELSE,
        RETURN,
        RETURNS,
        FOR,
        WHILE,
        BREAK,
        CONTINUE,
        FUNC,
        STRUCT,
        PLUS,
        MINUS,
        TIMES,
        DIVIDE,
        POWER,
        ASSIGN,
        EQ,
        LT,
        LE,
        GT,
        GE,
        NE,
        AND,
        OR,
        NOT,
        LPAREN,
        RPAREN,
        LBRACE,
        RBRACE,
        LBRACK,
        RBRACK,
        COMMA,
    }

    # The name can be Unicode as long as it does not start with a number (or dot).
    ID = r"[^\W\d][\w\.]*"

    # keywords
    ID["true"] = TRUE
    ID["false"] = FALSE
    ID["nil"] = NIL
    ID["if"] = IF
    ID["else"] = ELSE
    ID["return"] = RETURN
    ID["returns"] = RETURNS
    ID["for"] = FOR
    ID["while"] = WHILE
    ID["break"] = BREAK
    ID["continue"] = CONTINUE
    ID["func"] = FUNC
    ID["struct"] = STRUCT

    # operators
    PLUS = r"\+"
    MINUS = r"\-"
    TIMES = r"\*"
    DIVIDE = r"/"
    POWER = r"\^"

    EQ = r"=="
    ASSIGN = r"="

    # comparisons
    LE = r"<="
    LT = r"<"
    GE = r">="
    GT = r">"
    NE = r"!="

    # boolean operators
    OR = r"\|\|"
    AND = r"\&\&"
    NOT = r"\!"

    LPAREN = r"\("
    RPAREN = r"\)"
    LBRACK = r"\["
    RBRACK = r"\]"
    LBRACE = r"\{"
    RBRACE = r"\}"
    COMMA = r","

    @_(r"\d+")
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    # both single and double quoted strings are vaild
    @_(
        r"\"[^\"]*\"",
        r"'[^']*'",
    )
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t


@dataclass
class Variable:
    # If the value is None, the variable name will be looked up in the current scope.
    name: Optional[str]
    value: Any = None
    context: Literal["get", "set", "delete"] = "get"


class FunctionCall(Variable):
    pass


@dataclass
class BinaryOp:
    op: str
    left: Union[BinaryOp, Variable]
    right: Union[BinaryOp, Variable]


@dataclass
class Body:
    # A declaration can be a Variable, Function, or Struct.
    decls: List[Any]


@dataclass
class Function:
    name: str
    args: List[str]
    body: Body


@dataclass
class Struct:
    name: str
    args: List[str]


@dataclass
class Conditional:
    name: str
    cond: Optional[Union[BinaryOp, Variable]]
    body: Body


class Parser(sly.Parser):
    tokens = Lexer.tokens
    debugfile = "parser.out"

    precedence = (
        ("left", OR),
        ("left", AND),
        ("left", NOT),
        ("left", EQ, LE, LT, GT, GE, NE),
        ("left", PLUS, MINUS),
        ("left", TIMES, DIVIDE),
        ("left", POWER),
    )

    @_("{ declaration }")
    def body(self, p):
        return Body(decls=[d[0] for d in p[0]])

    @_("statement", "func", "struct", "cond")
    def declaration(self, p):
        return p[0]

    @_("FUNC ID LPAREN [ args ] RPAREN LBRACE body RBRACE")
    def func(self, p):
        return Function(p.ID, p.args, p.body)

    @_("STRUCT ID LBRACE args RBRACE")
    def struct(self, p):
        return Struct(p.ID, p.args)

    @_("ID { COMMA ID }")
    def args(self, p):
        return [p[0], *[a[1] for a in p[1]]]

    @_("cond_if { cond_elseif } [ cond_else ]")
    def cond(self, p):
        return [p.cond_if, *p.cond_elseif, p.cond_else]

    @_("IF expr LBRACE body RBRACE")
    def cond_if(self, p):
        return Conditional("if", p.expr, p.body)

    @_("ELSE cond_if")
    def cond_elseif(self, p):
        p[1].name = "else if"
        return p[1]

    @_("ELSE LBRACE body RBRACE")
    def cond_else(self, p):
        return Conditional("else", None, p.body)

    @_("ID ASSIGN expr")
    def statement(self, p):
        return Variable(p.ID, p.expr, context="set")

    @_(
        "ID PLUS ASSIGN expr",
        "ID MINUS ASSIGN expr",
        "ID TIMES ASSIGN expr",
        "ID DIVIDE ASSIGN expr",
        "ID POWER ASSIGN expr",
    )
    def statement(self, p):
        # statements like var += 1 are always expanded into var = var + 1
        binop = BinaryOp(p[1], Variable(p.ID), p.expr)
        return Variable(p.ID, binop, context="set")

    @_(
        "expr PLUS expr",
        "expr MINUS expr",
        "expr TIMES expr",
        "expr DIVIDE expr",
        "expr POWER expr",
        "expr EQ expr",
        "expr LE expr",
        "expr LT expr",
        "expr GE expr",
        "expr GT expr",
        "expr NE expr",
        "expr AND expr",
        "expr OR expr",
        "expr NOT expr",
    )
    def expr(self, p):
        return BinaryOp(p[1], p.expr0, p.expr1)

    @_("STRING", "NUMBER")
    def expr(self, p):
        return Variable(None, p[0])

    @_("ID")
    def expr(self, p):
        return Variable(p.ID, None, context="set")

    @_("LPAREN expr RPAREN")
    def expr(self, p):
        return p.expr

    @_("ID LPAREN RPAREN")
    def expr(self, p):
        return FunctionCall(p.ID, [])

    @_("expr { COMMA expr }")
    def func_call_args(self, p):
        return [p[0], *[a[1] for a in p[1]]]

    @_("")
    def empty(self, p):
        pass
