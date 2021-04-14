# coding: utf8
"""Python implementation of oxlang.
Inspired by the Cub Programming Language created by Louis D'hauwe.
"""

from pyparsing import (
    delimitedList,
    restOfLine,
    Char,
    Combine,
    Forward,
    Group,
    Keyword,
    Literal,
    MatchFirst,
    Optional,
    QuotedString,
    Suppress,
    pyparsing_common as pp_c,
)

__version__ = "0.0.1a0"

# symbols
(
    L_BRACE,
    R_BRACE,
    L_BRACK,
    R_BRACK,
    L_PAREN,
    R_PAREN,
    LESS_THAN,
    MORE_THAN,
    COMMA,
) = [Suppress(c) for c in "{}[]()<>,"]

EQUALS = Char("=")
OPERATOR = Char("+-/*^")

KEYWORDS = {
    keyword: Keyword(keyword)
    for keyword in "true false nil if else return for while break continue func struct".split()
}
KEYWORD = MatchFirst(KEYWORDS.values()).setName("keyword")

identifier = ~KEYWORD + pp_c.identifier
comment = Literal("//") + restOfLine

expr = Forward()

string = QuotedString("'") | QuotedString('"')
number = pp_c.number
boolean = KEYWORDS["true"] | KEYWORDS["false"]
nil = KEYWORDS["nil"]

value = string | number | boolean | nil | identifier
atom = value | Group(L_PAREN + expr + R_PAREN)

expr <<= atom + (OPERATOR + atom)[...]

assignment = identifier + Combine(Optional(OPERATOR) + EQUALS) + expr
