# coding: utf8
"""ox's core syntax lexer and parser."""

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
    for keyword in "true false nil if else return returns for while break continue func struct".split()
}
KEYWORDS["returns"] = KEYWORDS["returns"].suppress()
KEYWORD = MatchFirst(KEYWORDS.values()).setName("keyword")


def _parser():

    # basic syntax
    identifier = ~KEYWORD + pp_c.identifier
    comment = Literal("//") + restOfLine

    expr = Forward()

    string = QuotedString("'") | QuotedString('"')
    number = pp_c.number
    boolean = KEYWORDS["true"] | KEYWORDS["false"]
    nil = KEYWORDS["nil"]
    array = Group(L_BRACK + delimitedList(expr) + R_BRACK)

    function_call = Group(
        identifier("name")
        + L_PAREN
        + Optional(Group(expr) + Group(COMMA + expr)[...])("args")
        + R_PAREN
    )

    value = function_call | string | number | boolean | nil | array | identifier
    atom = value | Group(L_PAREN + expr + R_PAREN)

    # comparisons (i.e <=, >=, ==) return a boolean.
    comparison = Combine(((LESS_THAN | MORE_THAN) + Optional(EQUALS)) | EQUALS[2])

    # they can be chained like normal operators.
    expr <<= atom + ((OPERATOR | comparison) + atom)[...]

    assignment = Group(
        identifier("name")
        + Combine(Optional(OPERATOR) + EQUALS)("operator")
        + expr("expr")
    )

    # constructs
    args = delimitedList(identifier)

    struct = Group(
        KEYWORDS["struct"]
        + identifier("name")
        + Group(L_BRACE + args + R_BRACE)("args")
    )

    body = Forward()

    scoped_body = Group(L_BRACE + body + R_BRACE)

    if_condition = Group(KEYWORDS["if"] + expr)
    condition_header = (
        if_condition | (KEYWORDS["else"] + if_condition) | KEYWORDS["else"]
    )
    condition = condition_header + scoped_body

    # TODO: add type specification to args and struct
    function_header = Group(
        KEYWORDS["func"]
        + identifier("name")
        + L_PAREN
        + Group(args)("args")
        + R_PAREN
        + Optional(KEYWORDS["returns"])
    )
    function = function_header + scoped_body

    return_expr = Group(KEYWORDS["return"] + expr("expr"))

    body <<= (struct | condition | function | return_expr | assignment)[1, ...]
    body.ignore(comment)

    return body


Parser = _parser()
