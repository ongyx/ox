# coding: utf8
# type: ignore
# flake8: noqa
"""ox's core syntax lexer and parser."""

import enum
import sys
import textwrap

import sly  # type: ignore
from sly import lex, yacc

from . import ast_ as ast
from .exceptions import ParserError

ERROR_TEMPLATE = textwrap.dedent(
    """
    {filename}: In {context}:
    {filename}:{line}:{pos}: error: {message}
    
    {code}
    {indent}{arrows}
    """
)

SINGLETONS = {"true": True, "false": False, "nil": None}

# Pragmas change the behaviour of both the interpreter and parser.
# Kind of like Python's 'from __future__ import ...'.
# Pragmas have the form 'import pragma.<name>' where name is the pragma to use.
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
        IN,
        WHILE,
        BREAK,
        CONTINUE,
        FUNC,
        STRUCT,
        IMPORT,
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
        ELLIPSIS,
    }

    COMMENT = r"//.*"
    # https://stackoverflow.com/a/33312193
    LONG_COMMENT = r"/\*[\s\S]*?\*/"

    # The name can be Unicode as long as it does not start with a number (or dot).
    ID = r"[^\W\d][\w\.\:]*"

    # keywords
    ID["true"] = TRUE
    ID["false"] = FALSE
    ID["nil"] = NIL
    ID["if"] = IF
    ID["else"] = ELSE
    ID["return"] = RETURN
    ID["returns"] = RETURNS
    ID["for"] = FOR
    ID["in"] = IN
    ID["while"] = WHILE
    ID["break"] = BREAK
    ID["continue"] = CONTINUE
    ID["func"] = FUNC
    ID["struct"] = STRUCT
    ID["import"] = IMPORT

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

    LPAREN = r"\("
    RPAREN = r"\)"
    LBRACK = r"\["
    RBRACK = r"\]"
    LBRACE = r"\{"
    RBRACE = r"\}"

    COMMA = ","
    ELLIPSIS = r"\.\.\."

    @_(r"\d+(\.\d+)?")
    def NUMBER(self, t):
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

    def error(self, t):
        self.index += 1
        # propagate errors to the parser
        return t


def _loc(prod):
    try:
        return prod.lineno, prod.index
    except AttributeError:
        return 0, 0


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
        self.filename = "<string>"
        self.pragmas = set()

        # keep track of the name of the parent context
        # i.e function/struct name
        self.context_stack = []

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

        return ast.Body(*_loc(p), decls=decls)

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
        "for_in_loop",
        "while_loop",
        "CONTINUE",
        "BREAK",
        "import_",
        "comment",
    )
    def declaration(self, p):
        return p[0]

    @_("IMPORT ID")
    def import_(self, p):
        module = p.ID

        if module.startswith("pragma"):

            _, __, pragma = module.partition(".")

            if "." in pragma:
                self.error(p._slice[1], msg=f"invalid pragma '{pragma}'")

            self.pragmas.add(Pragma[pragma.upper()])

        return ast.Import(*_loc(p), module)

    @_("COMMENT", "LONG_COMMENT")
    def comment(self, p):
        return ast.Comment(*_loc(p), p[0])

    @_("ID ASSIGN expr")
    def statement(self, p):
        return ast.Assign(*_loc(p), ast.Variable(*_loc(p), p.ID), p.expr)

    @_(
        "ID PLUS ASSIGN expr",
        "ID MINUS ASSIGN expr",
        "ID TIMES ASSIGN expr",
        "ID DIVIDE ASSIGN expr",
        "ID POWER ASSIGN expr",
    )
    def statement(self, p):
        # statements like var += 1 are always expanded into var = var + 1
        binop = ast.BinaryOp(*_loc(p), p[1], ast.Variable(*_loc(p), p.ID), p.expr)
        return ast.Assign(*_loc(p), ast.Variable(*_loc(p), p.ID), binop)

    @_("FUNC ID new_context LPAREN [ args ] RPAREN [ RETURNS ] LBRACE body RBRACE")
    def func(self, p):

        if p.RETURNS is not None and Pragma.CUB not in self.pragmas:
            self.error(
                p._slice[6],
                "'returns' in function declaration is invalid.\n"
                "If you want to enable backward compatibility for Cub code,\n"
                "put 'import pragma.cub' at the top of the file.",
                index=6,
                prod=p,
            )

        self.context_stack.pop()

        return ast.Function(*_loc(p), p.ID, p.args or [], p.body)

    @_("RETURN expr")
    def func_return(self, p):
        return ast.FunctionReturn(*_loc(p), p.expr)

    @_("STRUCT ID new_context [ LPAREN args RPAREN ] LBRACE args RBRACE")
    def struct(self, p):
        self.context_stack.pop()

        return ast.Struct(*_loc(p), p.ID, p.args1, p.args0)

    @_("ID { COMMA ID } [ ELLIPSIS ]")
    def args(self, p):
        args = [p[0], *[a[1] for a in p[1]]]
        if p[2][0] is not None:
            args[-1] += "..."
        return args

    @_("FOR ID IN expr LBRACE body RBRACE")
    def for_in_loop(self, p):
        return ast.ForInLoop(
            *_loc(p), var=ast.Variable(*_loc(p), name=p.ID), expr=p.expr, body=p.body
        )

    @_("FOR statement COMMA expr COMMA statement LBRACE body RBRACE")
    def for_loop(self, p):
        return ast.Loop(
            *_loc(p), p.expr, p.body, preloop=p.statement0, postloop=p.statement1
        )

    @_("WHILE expr LBRACE body RBRACE")
    def while_loop(self, p):
        return ast.Loop(*_loc(p), p.expr, p.body)

    @_("{ _cond }")
    def cond(self, p):
        chain = p._cond

        root_cond = chain[0]
        prev_cond = root_cond

        for cond in chain:
            # attach this cond to the previous one.
            prev_cond.orelse = cond
            prev_cond = cond

        return root_cond

    @_(
        "IF expr LBRACE body RBRACE",
        "ELSE IF expr LBRACE body RBRACE",
        "ELSE LBRACE body RBRACE",
    )
    def _cond(self, p):
        if len(p) > 4:
            return ast.Conditional(*_loc(p), p.expr, p.body)
        else:
            return p.body

    # index (i.e a[0])
    @_("expr index { index }")
    def expr(self, p):
        return ast.Index(*_loc(p), target=p.expr, by=[p.index0, *[i[0] for i in p[2]]])

    @_("LBRACK expr RBRACK")
    def index(self, p):
        return p.expr

    @_("LBRACK [ expr_args ] RBRACK")
    def expr(self, p):
        return ast.Array(*_loc(p), p.expr_args)

    @_("ID LPAREN [ expr_args ] RPAREN")
    def expr(self, p):
        return ast.Call(*_loc(p), name=p.ID, args=p.expr_args or [])

    @_("expr { COMMA expr }")
    def expr_args(self, p):
        return [p[0], *[a[1] for a in p[1]]]

    @_(
        "NOT expr",
        "MINUS expr",  # unary minus
    )
    def expr(self, p):
        return ast.UnaryOp(*_loc(p), p[0], p.expr)

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
    )
    def expr(self, p):
        return ast.BinaryOp(*_loc(p), p[1], p.expr0, p.expr1)

    @_("STRING")
    def expr(self, p):
        return ast.Constant(*_loc(p), p[0])

    @_("NUMBER")
    def expr(self, p):
        raw = p[0]
        if "." in raw:
            num = float(raw)
        else:
            num = int(raw)

        return ast.Constant(*_loc(p), num)

    @_("TRUE", "FALSE", "NIL")
    def expr(self, p):
        return ast.Constant(*_loc(p), SINGLETONS[p[0]])

    @_("ID")
    def expr(self, p):
        return ast.Variable(*_loc(p), p.ID)

    @_("LPAREN expr RPAREN")
    def expr(self, p):
        return p.expr

    @_("")
    def new_context(self, p):
        self.context_stack.append(f"{p[-2]} '{p[-1]}'")

    def parse(self, tokens, reset=True):
        if reset:
            self.pragmas.clear()
        return super().parse(tokens)

    def parse_text(self, code, filename=None):
        self.code = code.splitlines()

        if filename is not None:
            self.filename = filename

        tokens = self.lexer.tokenize(code)

        return self.parse(self.lexer.tokenize(code))

    def error(self, token, msg=None, index=None, prod=None):

        line = 0
        pos = 0
        message = msg or "Syntax error"
        code = "(no code here)"

        if isinstance(token, lex.Token):
            line = token.lineno - 1
            abspos = token.index

            pos = abspos - sum(len(line) for line in self.code[:line])
            pos -= line

            arrows_len = len(token.value) if token.type != "ERROR" else 1

            if self.code is not None:
                code = self.code[line]

        elif isinstance(token, yacc.YaccSymbol):
            line = prod._slice[index - 1].lineno - 1

            arrows_len = len(token.value[0])

            if self.code is not None:
                code = self.code[line]
                pos = code.find(token.value[0])

        # pos can be -1 if the token was on the first line,
        # or the YaccSymbol value is not in the same line as the previous token.
        # (which should not happen...)
        if pos < 0:
            pos = 0

        message = ERROR_TEMPLATE.format(
            filename=self.filename,
            context=self.context_stack[-1] if self.context_stack else "<global>",
            line=line,
            pos=pos,
            message=message,
            code=code,
            indent=" " * pos,
            arrows="^" * arrows_len,
        )

        # fail hard on syntax errors
        raise ParserError(message)
