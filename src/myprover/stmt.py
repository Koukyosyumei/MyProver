from abc import ABCMeta, abstractmethod
from .claim import Expr


class Stmt(metaclass=ABCMeta):
    @abstractmethod
    def variables(self):
        pass


class SkipStmt(Stmt):
    def __repr__(self):
        return f"(Skip)"

    def variables(self):
        return set()


class AssignStmt(Stmt):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def __repr__(self):
        return f"(Assign {self.var} {self.expr})"

    def variables(self):
        return {self.var, *self.expr.variables()}


class IfStmt(Stmt):
    def __init__(self, cond_expr: Expr, lb_stmt: Stmt, rb_stmt: Stmt):
        self.cond = cond_expr
        self.lb = lb_stmt if lb_stmt is not None else SkipStmt()
        self.rb = rb_stmt if rb_stmt is not None else SkipStmt()

    def __repr__(self):
        return f"(If {self.cond} {self.lb} {self.rb})"

    def variables(self):
        return {*self.cond.variables(), *self.lb.variables(), *self.rb.variables()}


class SeqStmt(Stmt):
    def __init__(self, s1: Stmt, s2: Stmt):
        self.s1 = s1 if s1 is not None else SkipStmt()
        self.s2 = s2 if s2 is not None else SkipStmt()

    def __repr__(self):
        return f"(Seq {self.s1} {self.s2})"

    def variables(self):
        return {*self.s1.variables(), *self.s2.variables()}


class AssumeStmt(Stmt):
    def __init__(self, e: Expr):
        self.e = e

    def __repr__(self):
        return f"(Assume {self.e})"

    def variables(self):
        return {*self.e.variables()}


class AssertStmt(Stmt):
    def __init__(self, e):
        self.e = e

    def __repr__(self):
        return f"(Assert {self.e})"

    def variables(self):
        return {*self.e.variables()}


class WhileStmt(Stmt):
    def __init__(self, invs, cond: Expr, body: Stmt):
        self.cond = cond
        self.invariants = invs
        self.body = body if body is not None else SkipStmt()

    def __repr__(self):
        return f"(While {self.cond} {self.body})"

    def variables(self):
        return {*self.body.variables()}


class HavocStmt(Stmt):
    def __init__(self, var):
        self.var = var

    def __repr__(self):
        return f"(Havoc {self.var})"

    def variables(self):
        return set()
