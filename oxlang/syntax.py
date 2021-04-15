# coding: utf8
# type: ignore
"""ox's core syntax lexer and parser."""

import sly
from anytree import Node


class Lexer(sly.Lexer):

    ignore_comment = r"//.*"
    ignore = " \t\n"

    tokens = {
        ID,
        STRING,
        NUMBER,
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
    }

    literals = {"(", ")", "[", "]", "{", "}", ","}

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
    AND = r"\&\&"
    OR = r"\|\|"
    NOT = r"\!"

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


class Parser(sly.Parser):
    tokens = Lexer.tokens

    precedence = (
        ("left", OR),
        ("left", AND),
        ("left", NOT),
        ("left", LE, LT, GE, GT, NE, EQ),
        ("left", PLUS, MINUS),
        ("left", TIMES, DIVIDE),
        ("left", POWER),
    )

    @_("expr PLUS expr", "expr MINUS expr", "expr TIMES expr", "expr DIVIDE expr")
    def expr(self, p):
        return Node(p[1], left=p.expr0, right=p.expr1)

    @_("'(' expr ')'")
    def expr(self, p):
        return p.expr

    @_("NUMBER")
    def expr(self, p):
        return p.NUMBER
