# coding: utf8

from typing import Optional

from . import ast_ as ast, syntax


BINOP_MAP = {
    "+": "__add__",
    "-": "__sub__",
    "*": "__mul__",
    "/": "__div__",
    "^": "__pow__",
    "==": "__eq__",
    "!=": "__ne__",
    "<": "__lt__",
    "<=": "__le__",
    ">": "__gt__",
    ">=": "__ge__",
}

UNOP_MAP = {
    "-": "__neg__",
    "!": "__bool__",
}


# for nested structs
def _deep_get(d, ks):
    v = d
    for k in ks:
        v = v[k]

    return v


class Runtime:
    def __init__(self):
        self.parser = syntax.Parser()

        # the global code namespace.
        self.context = {}

    def reset(self):
        self.context.clear()

    def execute(self, code: str, context: Optional[dict] = None):
        if context is None:
            # global context
            context = self.context

        body = self.parser.parse_text(code)
        self.visit(body, context)

    def visit(self, node: ast.Node, context: dict):
        visitor = getattr(self, f"visit_{node.__class__.__name__}", self.visit_generic)

        return visitor(node, context)

    def visit_generic(self, node, context):
        print(f"unimplemented visit for node {node}")

    def visit_Comment(self, node, context):
        pass

    def visit_Constant(self, node, context):
        return node.value

    def visit_Variable(self, node, context):
        name = node.name.split(".")

        for ctx in (context, self.context):
            if name[0] in ctx:
                value = ctx[name[0]]

                if isinstance(value, dict):
                    # maybe it is a nested struct or module
                    try:
                        return _deep_get(value, name[1:])
                    except (TypeError, KeyError):
                        pass

                else:
                    return value

        raise RuntimeError(f"undefined variable: {node.name}")

    def visit_Assign(self, node, context):
        context[node.var.name] = self.visit(node.value, context)

    def visit_Function(self, node, context):
        context[node.name] = node

    def visit_Struct(self, node, context):
        context[node.name] = node

    def visit_FunctionCall(self, node, context):
        function = context.get(node.name) or self.context.get(node.name)

        if function is None:
            raise RuntimeError(f"undefined function: {node.name}")

        elif not isinstance(function, (ast.Function, ast.Struct)):
            raise RuntimeError("can't call a non-function/struct")

        expected = len(function.args)
        got = len(node.args)

        if expected != got:
            raise RuntimeError(
                f"function/struct {function.name} expected {expected} args, got {got}"
            )

        # Create new scope for the function.
        # Nothing magic here, just map the arg name to the arg expression.
        f_context = {
            arg: self.visit(expr, context)
            for arg, expr in zip(function.args, node.args)
        }

        if isinstance(function, ast.Function):
            return self.visit(function.body, f_context)
        else:
            # the dict represents a struct
            return f_context

    def visit_FunctionReturn(self, node, context):
        return self.visit(node.expr, context)

    def visit_UnaryOp(self, node, context):
        return getattr(self.visit(node.right, context), UNOP_MAP[node.op])()

    def visit_BinaryOp(self, node, context):
        return getattr(self.visit(node.left, context), BINOP_MAP[node.op])(
            self.visit(node.right, context)
        )

    def visit_Body(self, node, context):
        for decl in node.decls:
            self.visit(decl, context)

    def visit_Array(self, node, context):
        return [self.visit(item, context) for item in node.exprs]

    def visit_Conditional(self, node, context):
        if self.visit(node.cond, context):
            self.visit(node.body, context)

        else:
            if node.orelse is not None:
                self.visit(node.orelse, context)

    def visit_Loop(self, node, context):
        if node.preloop is not None:
            self.visit(node.preloop, context)

        while True:
            if self.visit(node.cond, context):
                self.visit(node.body, context)

            if node.postloop is not None:
                self.visit(node.postloop, context)
