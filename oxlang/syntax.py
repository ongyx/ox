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
    COMMA,
) = [Suppress(c) for c in "{}[](),"]

LESS_THAN = Char("<")
MORE_THAN = Char(">")
EQUALS = Char("=")
OPERATOR = Char("+-/*^")

# keywords
(
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
) = [
    Keyword(keyword)
    for keyword in "true false nil if else return returns for while break continue func struct".split()
]

KEYWORD = (
    TRUE
    | FALSE
    | NIL
    | IF
    | ELSE
    | RETURN
    | RETURNS
    | FOR
    | WHILE
    | BREAK
    | CONTINUE
    | FUNC
    | STRUCT
)


def _parser():

    # basic syntax
    identifier = ~KEYWORD + pp_c.identifier
    comment = Literal("//") + restOfLine

    expr = Forward()

    string = QuotedString("'") | QuotedString('"')
    number = pp_c.number
    boolean = TRUE | FALSE
    nil = NIL
    array = Group(L_BRACK + Optional(delimitedList(expr)) + R_BRACK)

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
        STRUCT + identifier("name") + Group(L_BRACE + args + R_BRACE)("args")
    )

    body = Forward()
    scoped_body = Group(L_BRACE + body + R_BRACE)

    if_condition = Group(IF + expr)
    condition_header = if_condition | (ELSE + if_condition) | ELSE
    condition = condition_header + scoped_body

    for_header = FOR + Group(assignment + COMMA + assignment + COMMA + Group(expr))

    while_header = WHILE + Group(expr)

    global loop
    loop = Group((for_header | while_header) + scoped_body)

    # TODO: add type specification to args and struct
    function_header = Group(
        FUNC
        + identifier("name")
        + L_PAREN
        + Optional(Group(args)("args"))
        + R_PAREN
        + Optional(RETURNS)
    )
    function = function_header + scoped_body

    return_expr = Group(RETURN + expr("expr"))

    body <<= (
        struct
        | function
        | return_expr
        | loop
        | CONTINUE
        | BREAK
        | condition
        | assignment
        | expr  # function calls are also exprs (return value does not need to be assigned)
    )[1, ...]
    body.ignore(comment)

    return body


Parser = _parser()
