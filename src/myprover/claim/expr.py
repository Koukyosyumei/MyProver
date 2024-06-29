from abc import ABCMeta, abstractmethod

from .op import Op
from .value import Value, VInt


class Expr(metaclass=ABCMeta):
    @abstractmethod
    def collect_variables(self):
        pass

    @abstractmethod
    def substitute(self, old_var, new_var):
        pass


class VarExpr(Expr):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"(Var {self.name})"

    def collect_variables(self):
        return {self.name}

    def substitute(self, old_var, new_var):
        if self.name == old_var.name:
            return new_var
        else:
            return self


class SliceExpr(Expr):
    def __init__(self, lower: Expr, upper: Expr):
        self.lower = lower if lower is not None else LiteralExpr(VInt(0))
        self.upper = upper

    def __repr__(self):
        return f"(Slice {self.lower} -> {self.upper})"

    def substitute(self, old_var, new_var):
        return self

    def collect_variables(self, old_var, new_var):
        return {}


class SubscriptExpr(Expr):
    def __init__(self, var, subscript: Expr):
        self.var = var
        self.subscript = subscript

    def __repr__(self):
        return f"(Subscript {self.var} {self.subscript})"

    def collect_variables(self):
        return self.var.collect_variables().union(self.subscript.collect_variables())

    def substitute(self, old_var, new_var):
        return self


class LiteralExpr(Expr):
    def __init__(self, v: Value):
        self.value = v

    def __repr__(self):
        return f"(Literal {self.value})"

    def collect_variables(self):
        return set()

    def substitute(self, old_var, new_var):
        return self


class UnOpExpr(Expr):
    def __init__(self, op: Op, expr: Expr):
        self.op = op
        self.e = expr

    def __repr__(self):
        return f"(UnOp {self.op} {self.e})"

    def collect_variables(self):
        return {*self.e.collect_variables()}

    def substitute(self, old_var, new_var):
        return UnOpExpr(self.op, self.e.substitute(old_var, new_var))


class BinOpExpr(Expr):
    def __init__(self, l: Expr, op: Op, r: Expr):
        self.e1 = l
        self.e2 = r
        self.op = op

    def __repr__(self):
        return f"(BinOp {self.e1} {self.op} {self.e2})"

    def collect_variables(self):
        return {*self.e1.collect_variables(), *self.e2.collect_variables()}

    def substitute(self, old_var, new_var):
        return BinOpExpr(
            self.e1.substitute(old_var, new_var),
            self.op,
            self.e2.substitute(old_var, new_var),
        )


class QuantificationExpr(Expr):
    def __init__(self, quantifier, var, expr, var_type=None, bounded=False):
        self.quantifier = quantifier
        self.var = var
        self.var_type = var_type
        self.expr = expr
        self.bounded = bounded

    def sanitize(self):
        if self.bounded:
            return

        bounded_var = VarExpr(self.var.name + "$$0")
        e = self.expr.substitute(self.var, bounded_var)

        if self.quantifier == "EXISTS":
            # exists x. Q <==> not forall x. not Q
            return UnOpExpr(
                Op.Not,
                QuantificationExpr(
                    "FORALL", bounded_var, UnOpExpr(Op.Not, e), self.var_type, True
                ),
            )
        else:
            return QuantificationExpr("FORALL", bounded_var, e, self.var_type, True)

    def __repr__(self):
        return f"(forall  {self.var}:{self.var_type}. {self.expr})"

    def substitute(self, old_var, new_var):
        return QuantificationExpr(
            self.quantifier,
            self.var,
            self.expr.substitute(old_var, new_var),
            self.var_type,
            self.bounded,
        )

    def collect_variables(self, old_var, new_var):
        return {}
