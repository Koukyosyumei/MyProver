import ast
from functools import reduce

import z3

from .claim import (
    AssertStmt,
    AssignStmt,
    AssumeStmt,
    BinOpExpr,
    BoolValue,
    ClaimParser,
    CompoundStmt,
    IfElseStmt,
    IntValue,
    LiteralExpr,
    Op,
    QuantificationExpr,
    SkipStmt,
    SliceExpr,
    SubscriptExpr,
    UnOpExpr,
    VarExpr,
    DPAssignStmt,
    WhileStmt,
)


def is_invariant(y):
    return (
        isinstance(y, ast.Expr)
        and isinstance(y.value, ast.Call)
        and y.value.func.id == "invariant"
    )


class PyToClaim(ast.NodeVisitor):
    def walk_seq(self, stmts):
        if stmts:
            hd, *stmts = stmts
            t_node = self.visit(hd)
            while stmts:
                t2_node, stmts = (self.visit(stmts[0])), stmts[1:]
                t_node = CompoundStmt(t_node, t2_node)
            if not isinstance(t_node, CompoundStmt):
                return CompoundStmt(t_node, SkipStmt())
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
        return LiteralExpr(IntValue(node.n))

    def visit_NameConstant(self, node):
        return LiteralExpr(BoolValue(node.value))

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

    def visit_Compare(self, node):
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

    def visit_Call(self, node):
        if node.func.id == "assume":
            return AssumeStmt(ClaimParser(node.args[0].s).parse_expr())
        elif node.func.id == "invariant":
            return ClaimParser(node.args[0].s).parse_expr()

    def visit_Slice(self, node):
        lo, hi = [None] * 2
        if node.lower:
            lo = self.visit(node.lower)
        if node.upper:
            hi = self.visit(node.upper)
        # if node.step:
        #    step = self.visit(node.step)
        return SliceExpr(lo, hi)

    def visit_Subscript(self, node):
        return SubscriptExpr(self.visit(node.value), self.visit(node.slice))

    def visit_Constant(self, node):
        return LiteralExpr(IntValue(node.value))

    def visit_FunctionDef(self, node):
        return self.walk_seq(node.body)

    def visit_Module(self, node):
        return self.walk_seq(node.body)

    def visit_If(self, node):
        cond = self.visit(node.test)
        then_branch = self.walk_seq(node.body)
        rb = self.walk_seq(node.orelse)
        return IfElseStmt(cond, then_branch, rb)

    def visit_While(self, node):
        cond = self.visit(node.test)

        invariants = [self.visit_Call(x.value) for x in filter(is_invariant, node.body)]
        reduced_invariant = (
            LiteralExpr(BoolValue(True))
            if not invariants
            else reduce(lambda i1, i2: BinOpExpr(i1, Op.And, i2), invariants)
        )

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

        return WhileStmt(reduced_invariant, cond, body)

    def visit_Assert(self, node):
        return AssertStmt(self.visit(node.test))

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Subscript):
            var = self.visit(node.targets[0])
        else:
            varname = node.targets[0].id
            var = VarExpr(varname)
        return AssignStmt(var, self.visit(node.value))

    def visit_Return(self, node):
        return SkipStmt()

    def visit_Pass(self, node):
        return SkipStmt()

    def visit_Expr(self, node):
        return self.visit(node.value)


class PyToDPClaim(PyToClaim):
    def __init__(self, forked_vanames=set()):
        super().__init__()
        self.forked_varnames = forked_vanames

    def visit_Call(self, node):
        if node.func.id == "assume":
            return AssumeStmt(ClaimParser(node.args[0].s).parse_expr())
        elif node.func.id == "invariant":
            return ClaimParser(node.args[0].s).parse_expr()
        elif node.func.id == "laplace":
            e = self.visit(node.args[0])
            e_1 = e.clone()
            e_2 = e.clone()
            for vn in self.forked_varnames:
                e_1 = e_1.assign_variable(VarExpr(vn), VarExpr(vn + "#1"))
                e_2 = e_2.assign_variable(VarExpr(vn), VarExpr(vn + "#2"))
            return DPAssignStmt(
                VarExpr("v_eps#"),
                BinOpExpr(
                    VarExpr("v_eps#"),
                    Op.Add,
                    BinOpExpr(
                        UnOpExpr(Op.Abs, BinOpExpr(e_1, Op.Minus, e_2)),
                        Op.Mult,
                        VarExpr("eps#"),
                    ),
                ),
            )

    def visit_If(self, node):
        cond = self.visit(node.test)

        cond_1 = cond.clone()
        cond_2 = cond.clone()
        for vn in self.forked_varnames:
            cond_1 = cond_1.assign_variable(VarExpr(vn), VarExpr(vn + "#1"))
            cond_2 = cond_2.assign_variable(VarExpr(vn), VarExpr(vn + "#2"))

        then_branch = self.walk_seq(node.body)
        rb = self.walk_seq(node.orelse)
        return CompoundStmt(
            AssertStmt(BinOpExpr(cond_1, Op.Iff, cond_2)),
            IfElseStmt(cond_1, then_branch, rb),
        )

    def visit_While(self, node):
        cond = self.visit(node.test)

        cond_1 = cond.clone()
        cond_2 = cond.clone()
        for vn in self.forked_varnames:
            cond_1 = cond_1.assign_variable(VarExpr(vn), VarExpr(vn + "#1"))
            cond_2 = cond_2.assign_variable(VarExpr(vn), VarExpr(vn + "#2"))

        invariants = [self.visit_Call(x.value) for x in filter(is_invariant, node.body)]
        reduced_invariant = (
            LiteralExpr(BoolValue(True))
            if not invariants
            else reduce(lambda i1, i2: BinOpExpr(i1, Op.And, i2), invariants)
        )

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
        body = CompoundStmt(body, AssertStmt(BinOpExpr(cond_1, Op.Iff, cond_2)))

        return CompoundStmt(
            AssertStmt(BinOpExpr(cond_1, Op.Iff, cond_2)),
            WhileStmt(reduced_invariant, cond_1, body),
        )

    def visit_Assert(self, node):
        return AssertStmt(self.visit(node.test))

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Subscript):
            left_expr = self.visit(node.targets[0])
            left_varname = left_expr.var.name
        else:
            left_varname = node.targets[0].id

        right_expr = self.visit(node.value)
        right_expr_1 = right_expr.clone()
        right_expr_2 = right_expr.clone()
        for vn in self.forked_varnames:
            right_expr_1 = right_expr_1.assign_variable(VarExpr(vn), VarExpr(vn + "#1"))
            right_expr_2 = right_expr_2.assign_variable(VarExpr(vn), VarExpr(vn + "#2"))

        if isinstance(node.targets[0], ast.Subscript):
            left_expr_1 = left_expr.clone()
            left_expr_2 = left_expr.clone()
            for vn in self.forked_varnames:
                left_expr_1 = left_expr_1.assign_variable(
                    VarExpr(vn), VarExpr(vn + "#1")
                )
                left_expr_2 = left_expr_2.assign_variable(
                    VarExpr(vn), VarExpr(vn + "#2")
                )

            if isinstance(right_expr, DPAssignStmt):
                return CompoundStmt(
                    AssumeStmt(BinOpExpr(left_expr_1, Op.Eq, left_expr_2)), right_expr
                )
            else:
                return CompoundStmt(
                    AssignStmt(left_expr_1, right_expr_1),
                    AssignStmt(left_expr_2, right_expr_2),
                )
        else:
            if isinstance(right_expr, DPAssignStmt):
                return CompoundStmt(
                    AssumeStmt(
                        BinOpExpr(
                            VarExpr(left_varname + "#1"),
                            Op.Eq,
                            VarExpr(left_varname + "#2"),
                        )
                    ),
                    right_expr,
                )
            else:
                return CompoundStmt(
                    AssignStmt(VarExpr(left_varname + "#1"), right_expr_1),
                    AssignStmt(VarExpr(left_varname + "#2"), right_expr_2),
                )


class ClaimToZ3:
    def __init__(self, name_dict):
        self.name_dict = name_dict

    def visit(self, expr):
        if isinstance(expr, LiteralExpr):
            return self.visit_Literal(expr)
        elif isinstance(expr, VarExpr):
            return self.visit_Var(expr)
        elif isinstance(expr, BinOpExpr):
            return self.visit_BinOp(expr)
        elif isinstance(expr, UnOpExpr):
            return self.visit_Unop(expr)
        elif isinstance(expr, QuantificationExpr):
            return self.visit_Quantification(expr)
        elif isinstance(expr, SubscriptExpr):
            return self.visit_Subscript(expr)
        else:
            raise NotImplementedError(f"`{type(expr)} is not supported")

    def visit_Literal(self, node):
        return node.value.v

    def visit_Var(self, node):
        if node.name in self.name_dict:
            return self.name_dict[node.name]
        elif node.name.split("#")[0] in self.name_dict:
            return self.name_dict[node.name.split("#")[0]]
        else:
            raise KeyError(f"{node.name} is unkonwn in name_dict when converting Claim to Z3")
        # return self.name_dict[node.name]

    def visit_Subscript(self, node):
        return z3.Select(self.name_dict[node.var.name], self.visit(node.subscript))

    def visit_BinOp(self, node):
        c1 = self.visit(node.e1)
        c2 = self.visit(node.e2)

        if node.op == Op.Add:
            return c1 + c2
        elif node.op == Op.Minus:
            return c1 - c2
        elif node.op == Op.Mult:
            return c1 * c2
        elif node.op == Op.Div:
            return c1 / c2
        elif node.op == Op.Mod:
            return c1 % c2
        elif node.op == Op.And:
            return z3.And(c1, c2)
        elif node.op == Op.Or:
            return z3.Or(c1, c2)
        elif node.op == Op.Implies:
            return z3.Implies(c1, c2)
        elif node.op == Op.Iff:
            return z3.And(z3.Implies(c1, c2), z3.Implies(c2, c1))
        elif node.op == Op.Eq:
            return c1 == c2
        elif node.op == Op.NEq:
            return z3.Not(c1 == c2)
        elif node.op == Op.Gt:
            return c1 > c2
        elif node.op == Op.Ge:
            return c1 >= c2
        elif node.op == Op.Lt:
            return c1 < c2
        elif node.op == Op.Le:
            return c1 <= c2
        else:
            raise NotImplementedError(f"{node.op} is not supported")

    def visit_Unop(self, node):
        c = self.visit(node.e)
        if node.op == Op.Minus:
            return -c
        elif node.op == Op.Not:
            return z3.Not(c)
        elif node.op == Op.Abs:
            return z3.If(c > 0, c, -c)
        else:
            raise NotImplementedError(f"{node.op} is not supported")

    def visit_Quantification(self, node):
        if node.var_type == int:
            z3_var = z3.Int(node.var.name)
        elif node.var_type == bool:
            z3_var = z3.Bool(node.var.name)
        elif node.var_type == list[int]:
            z3_var = z3.Array(node.var.name, z3.IntSort(), z3.IntSort())
        else:
            raise NotImplementedError(f"{node.var_type} is not supported")
        self.name_dict[node.var.name] = z3_var
        return z3.ForAll(z3_var, self.visit(node.expr))
