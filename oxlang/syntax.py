# coding: utf8
# type: ignore
# flake8: noqa
"""ox's core syntax lexer and parser."""

import sly

from . import ast_ as ast


SINGLETONS = {"true": True, "false": False, "nil": None}

# Pragmas change the behaviour of both the interpreter and parser.
# Kind of like Python's 'from __future__ import ...'.
# Pragmas have the form 'pragma <name>' where name is the pragma to use.
# Multiple pragmas may be declared (for now).
PRAGMAS = {
    # Allows 'returns' in a function declaration (idk why Cub needed that):
    # func myFunc() returns {
    # TODO: Alias global functions used in Cub
    "cub",
}


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
        PRAGMA,
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
    ID["pragma"] = PRAGMA

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

    @_(r"\d+(\.\d+)?")
    def NUMBER(self, t):
        if "." in t.value:
            t.value = float(t.value)
        else:
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

    def __init__(self):
        self.pragmas = set()

    @_("{ declaration }")
    def body(self, p):
        decls = []
        for decl in p[0]:
            decl = decl[0]
            if isinstance(decl, list):
                # condition is in a nested tuple, so get rid of it
                decls.extend([d[0] for d in decl])
            else:
                decls.append(decl)

        return ast.Body(decls=decls)

    # Not assigning the expr to a variable is valid.
    # i.e function calls: myFunc()
    @_(
        "expr",
        "statement",
        "func",
        "func_return",
        "struct",
        "{ cond }",
        "for_loop",
        "while_loop",
        "CONTINUE",
        "BREAK",
        "pragma",
    )
    def declaration(self, p):
        return p[0]

    @_("ID ASSIGN expr")
    def statement(self, p):
        return ast.Variable(p.ID, p.expr, op="set")

    @_(
        "ID PLUS ASSIGN expr",
        "ID MINUS ASSIGN expr",
        "ID TIMES ASSIGN expr",
        "ID DIVIDE ASSIGN expr",
        "ID POWER ASSIGN expr",
    )
    def statement(self, p):
        # statements like var += 1 are always expanded into var = var + 1
        binop = ast.BinaryOp(p[1], ast.Variable(p.ID), p.expr)
        return ast.Variable(p.ID, binop, op="set")

    @_("FUNC ID LPAREN [ args ] RPAREN [ RETURNS ] LBRACE body RBRACE")
    def func(self, p):

        if p.RETURNS is not None and "cub" not in self.pragmas:
            self.log.warning(
                "'returns' in function declaration is depreciated (only for Cub compatiblity).\n"
                "If you want to suppress this, put 'pragma \"cub\"' at the top of the file."
            )

        return ast.Function(p.ID, p.args, p.body)

    @_("RETURN expr")
    def func_return(self, p):
        return ast.FunctionReturn(p.expr)

    @_("STRUCT ID LBRACE args RBRACE")
    def struct(self, p):
        return ast.Struct(p.ID, p.args)

    @_("ID { COMMA ID }")
    def args(self, p):
        return [p[0], *[a[1] for a in p[1]]]

    @_("FOR statement COMMA expr COMMA statement LBRACE body RBRACE")
    def for_loop(self, p):
        return ast.Loop(p.expr, p.body, preloop=p.statement0, postloop=p.statement1)

    @_("WHILE expr LBRACE body RBRACE")
    def while_loop(self, p):
        return ast.Loop(p.expr, p.body)

    @_("cond_if", "cond_elseif", "cond_else")
    def cond(self, p):
        return p[0]

    @_("ELSE LBRACE body RBRACE")
    def cond_else(self, p):
        return ast.Conditional("else", None, p.body)

    @_("ELSE IF expr LBRACE body RBRACE")
    def cond_elseif(self, p):
        return ast.Conditional("else if", p.expr, p.body)

    @_("IF expr LBRACE body RBRACE")
    def cond_if(self, p):
        return ast.Conditional("if", p.expr, p.body)

    @_("LBRACK [ array_literals ] RBRACK")
    def expr(self, p):
        return p.array_literals

    @_("expr { COMMA expr }")
    def array_literals(self, p):
        return ast.Array([p[0], *[e[1] for e in p[1]]])

    @_("ID LPAREN [ func_call_args ] RPAREN")
    def expr(self, p):
        return ast.FunctionCall(p.ID, p.func_call_args)

    @_("expr { COMMA expr }")
    def func_call_args(self, p):
        return [p[0], *[a[1] for a in p[1]]]

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
        return ast.BinaryOp(p[1], p.expr0, p.expr1)

    @_("STRING", "NUMBER")
    def expr(self, p):
        return ast.Variable(None, p[0])

    @_("TRUE", "FALSE", "NIL")
    def expr(self, p):
        return ast.Variable(None, SINGLETONS[p[0]])

    @_("ID")
    def expr(self, p):
        return ast.Variable(p.ID, None, op="get")

    @_("LPAREN expr RPAREN")
    def expr(self, p):
        return p.expr

    @_("PRAGMA STRING")
    def pragma(self, p):
        self.pragmas.add(p.STRING)

    @_("")
    def empty(self, p):
        pass

    def parse(self, tokens, reset=True):
        if reset:
            self.pragmas.clear()
        return super().parse(tokens)

    def error(self, t):
        super().error(t)
        # crash hard on syntax errors
        raise RuntimeError()
