import ast
from functools import reduce

from .stmt import (
    HavocStmt,
    IfStmt,
    SeqStmt,
    AssumeStmt,
    AssertStmt,
    SkipStmt,
    AssignStmt,
)
from .parser import (
    UnOpExpr,
    VarExpr,
    SubscriptExpr,
    Parser,
    LiteralExpr,
    VInt,
    VBool,
    BinOpExpr,
    Op,
)


def is_invariant(y):
    return (
        isinstance(y, ast.Expr)
        and isinstance(y.value, ast.Call)
        and y.value.func.id == "invariant"
    )


class Py2AssernTranslator(ast.NodeVisitor):
    def walk_seq(self, stmts, need_visit=True):
        if stmts:
            hd, *stmts = stmts
            t_node = self.visit(hd) if need_visit else hd
            while stmts:
                t2_node, stmts = (
                    self.visit(stmts[0]) if need_visit else stmts[0]
                ), stmts[1:]
                t_node = SeqStmt(t_node, t2_node)
            if not isinstance(t_node, SeqStmt):
                return SeqStmt(t_node, SkipStmt())
            return t_node
        else:
            return SkipStmt()

    def fold_binops(self, op, values):
        result = BinOpExpr(self.visit(values[0]), op, self.visit(values[1]))
        for e in values[2:]:
            result = BinOpExpr(result, op, self.visit(e))
        return result

    def visit_Name(self, node):
        return VarExpr(node.id)

    def visit_Num(self, node):
        return LiteralExpr(VInt(node.n))

    def visit_NameConstant(self, node):
        return LiteralExpr(VBool(node.value))

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_BoolOp(self, node):
        if type(node.op) == ast.And:
            op = Op.And
        elif type(node.op) == ast.Or:
            op = Op.Or
        else:
            raise ValueError(f"{node.op} is not supported")
        return self.fold_binops(op, node.values)

    def visit_compare(self, node):
        lv = self.visit(node.left)
        rv = self.visit(node.comparators[0])
        if type(node.ops[0]) == ast.Lt:
            op = Op.Lt
        elif type(node.ops[0]) == ast.LtE:
            op = Op.Le
        elif type(node.ops[0]) == ast.Gt:
            op = Op.Gt
        elif type(node.ops[0]) == ast.GtE:
            op = Op.Ge
        elif type(node.ops[0]) == ast.Eq:
            op = Op.Eq
        elif type(node.ops[0]) == ast.NotEq:
            op = Op.NEq
        else:
            raise ValueError(f"{node.op} is not supported")
        return BinOpExpr(lv, op, rv)

    def visit_BinOp(self, node):
        lv = self.visit(node.left)
        rv = self.visit(node.right)
        if type(node.op) == ast.Add:
            op = Op.Add
        elif type(node.op) == ast.Sub:
            op = Op.Minus
        elif type(node.op) == ast.Mult:
            op = Op.Mult
        elif type(node.op) == ast.Div:
            op = Op.Div
        elif type(node.op) == ast.Mod:
            op = Op.Mod
        else:
            raise ValueError(f"{node.op} is not supported")
        return BinOpExpr(lv, op, rv)

    def visit_UnaryOp(self, node):
        v = self.visit(node.operand)
        if type(node.op) == ast.USub:
            op = Op.Minus
        elif type(node.op) == ast.Not:
            op = Op.Not
        else:
            raise ValueError(f"{node.op} is not supported")
        return UnOpExpr(op, v)

    def visit_Index(self, node):
        return self.visit(node.value)

    def visit_Subscript(self, node):
        return SubscriptExpr(self.visit(node.value), self.visit(node.slice))

    def visit_Constant(self, node):
        return LiteralExpr(VInt(node.value))

    def visit_Module(self, node):
        return self.walk_seq(node.body)

    def visit_If(self, node):
        cond = self.visit(node.test)
        lb = self.walk_seq(node.body)
        rb = self.walk_seq(node.orelse)
        return IfStmt(cond, lb, rb)

    def visit_While(self, node):
        cond = self.visit(node.test)
        invars = [self.visit_Call(x.value) for x in filter(is_invariant, node.body)]
        body = self.walk_seq(
            list(
                filter(
                    lambda x: (
                        True
                        if not isinstance(x, ast.Expr)
                        or not isinstance(x.value, ast.Call)
                        else x.value.func.id != "invariant"
                    ),
                    node.body,
                )
            )
        )
        loop_targets = body.variables()
        havocs = list(map(HavocStmt, loop_targets))
        invariants = (
            LiteralExpr(VBool(True))
            if not invars
            else reduce(lambda i1, i2: BinOpExpr(i1, Op.And, i2), invars)
        )
        return self.walk_seq(
            [
                AssertStmt(invariants),
                *havocs,
                AssumeStmt(invariants),
                IfStmt(
                    cond,
                    self.walk_seq(
                        [
                            body,
                            AssertStmt(invariants),
                            AssumeStmt(LiteralExpr(VBool(False))),
                        ],
                        need_visit=False,
                    ),
                    SkipStmt(),
                ),
            ],
            need_visit=False,
        )

    def visit_Assert(self, node):
        return AssertStmt(self.visit(node.test))

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Subscript):
            varname = self.visit(node.targets[0])
        else:
            varname = node.targets[0].id
        return AssignStmt(varname, self.visit(node.value))

    def visit_Return(self, node):
        return SkipStmt()

    def visit_Call(self, node):
        if node.func.id == "assume":
            return AssumeStmt(Parser(node.args[0].s).parse_expr())
        elif node.func.id == "invariant":
            return Parser(node.args[0].s).parse_expr()

    def visit_Pass(self, node):
        return SkipStmt()

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit(self, node):
        return super().visit(node)
