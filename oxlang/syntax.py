# coding: utf8
# type: ignore
# flake8: noqa
"""ox's core syntax lexer and parser."""

import enum
import sys
import textwrap

import sly
from sly import lex, yacc

from . import ast_ as ast
from .exceptions import ParserError

SINGLETONS = {"true": True, "false": False, "nil": None}

# Pragmas change the behaviour of both the interpreter and parser.
# Kind of like Python's 'from __future__ import ...'.
# Pragmas have the form 'pragma <name>' where name is the pragma to use.
# Multiple pragmas may be declared (for now).
class Pragma(enum.Enum):
    # Allows 'returns' in a function declaration (idk why Cub needed that):
    # func myFunc() returns {
    # TODO: Alias global functions used in Cub
    CUB = 0


class Lexer(sly.Lexer):

    ignore = " \t"

    tokens = {
        COMMENT,
        LONG_COMMENT,
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

    COMMENT = r"//.*"
    # https://stackoverflow.com/a/33312193
    LONG_COMMENT = r"/\*[\s\S]*?\*/"

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

    @_(r"\n+")
    def ignore_newline(self, t):
        self.lineno += len(t.value)


class Parser(sly.Parser):
    tokens = Lexer.tokens
    debugfile = "parser.out"
    lexer = Lexer()

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
        self.code = None
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
        "comment",
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

        if p.RETURNS is not None and Pragma.CUB not in self.pragmas:
            self.error(
                p._slice[5],
                "'returns' in function declaration is invalid.\n"
                "If you want to enable backward compatibility,\n"
                "put 'pragma \"cub\"' at the top of the file.",
                index=5,
                prod=p,
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
        self.pragmas.add(Pragma[p.STRING.upper()])

    @_("")
    def empty(self, p):
        pass

    @_("COMMENT", "LONG_COMMENT")
    def comment(self, p):
        return ast.Comment(p[0])

    def parse(self, tokens, reset=True):
        if reset:
            self.pragmas.clear()
        return super().parse(tokens)

    def parse_text(self, code):
        self.code = code.splitlines()
        return self.parse(self.lexer.tokenize(code))

    def error(self, token, msg=None, index=None, prod=None):

        line = 0
        pos = 0
        message = msg or "Syntax error"
        code = "(no code here)"

        if isinstance(token, lex.Token):
            line = token.lineno - 1
            abspos = token.index

            # +1 line length for the newline...
            pos = abspos - sum(len(line) + 1 for line in self.code[:line])
            # ...and minus one for the newline just before the token's line.
            pos -= 1

            if self.code is not None:
                code = self.code[line]

        elif isinstance(token, yacc.YaccSymbol):
            line = prod._slice[index - 1].lineno - 1

            if self.code is not None:
                code = self.code[line]
                pos = code.find(token.value[0])

        # pos can be -1 if the token was on the first line,
        # or the YaccSymbol value is not in the same line as the previous token.
        # (which should not happen...)
        if pos < 0:
            pos = 0

        message = textwrap.dedent(
            """
            ERROR:{line}:{pos}: {message}
            
            {code}
            {indent}^
            """
        ).format(line=line, pos=pos, message=message, code=code, indent=" " * pos)

        # fail hard on syntax errors
        raise ParserError(message)
