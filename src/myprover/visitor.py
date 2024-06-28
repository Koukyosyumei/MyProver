import ast
from functools import reduce

import z3

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
    SliceExpr,
    QuantificationExpr,
    Op,
)
from .type import TypeINT, TypeBOOL


def is_invariant(y):
    return (
        isinstance(y, ast.Expr)
        and isinstance(y.value, ast.Call)
        and y.value.func.id == "invariant"
    )


class PyToClaim(ast.NodeVisitor):
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
            return AssumeStmt(Parser(node.args[0].s).parse_expr())
        elif node.func.id == "invariant":
            return Parser(node.args[0].s).parse_expr()

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

    def visit_Pass(self, node):
        return SkipStmt()

    def visit_Expr(self, node):
        return self.visit(node.value)
    
    
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
        else:
            raise NotImplementedError(f"`{type(expr)} is not supported")

    def visit_Literal(self, node):
        node.value.v

    def visit_Var(self, node):
        return self.name_dict[node.name]
    
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
        if node.op == Op.NEq:
            return -c
        elif node.op == Op.Not:
            return z3.Not(c)
        else:
            raise NotImplementedError(f"{node.op} is not supported")
        
    def visit_Quantification(self, node):
        if isinstance(node.var_type, TypeINT):
            self.name_dict[node.var.name] = z3.Int(node.var.name)
        elif isinstance(node.var_type, TypeBOOL):
            self.name_dict[node.var.name] = z3.Bool(node.var.name)
        else:
            raise NotImplementedError(f"{node.var_type} is not supported")