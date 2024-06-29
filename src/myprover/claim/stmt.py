from abc import ABCMeta, abstractmethod

from .expr import Expr


class Stmt(metaclass=ABCMeta):
    @abstractmethod
    def collect_variables(self):
        pass


class SkipStmt(Stmt):
    def __repr__(self):
        return f"(Skip)"

    def collect_variables(self):
        return set()


class AssignStmt(Stmt):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def __repr__(self):
        return f"(Assign {self.var} {self.expr})"

    def collect_variables(self):
        return {self.var, *self.expr.collect_variables()}


class IfStmt(Stmt):
    def __init__(self, cond_expr: Expr, lb_stmt: Stmt, rb_stmt: Stmt):
        self.cond = cond_expr
        self.lb = lb_stmt if lb_stmt is not None else SkipStmt()
        self.rb = rb_stmt if rb_stmt is not None else SkipStmt()

    def __repr__(self):
        return f"(If {self.cond} {self.lb} {self.rb})"

    def collect_variables(self):
        return {
            *self.cond.collect_variables(),
            *self.lb.collect_variables(),
            *self.rb.collect_variables(),
        }


class SeqStmt(Stmt):
    def __init__(self, s1: Stmt, s2: Stmt):
        self.s1 = s1 if s1 is not None else SkipStmt()
        self.s2 = s2 if s2 is not None else SkipStmt()

    def __repr__(self):
        return f"(Seq {self.s1} {self.s2})"

    def collect_variables(self):
        return {*self.s1.collect_variables(), *self.s2.collect_variables()}


class AssumeStmt(Stmt):
    def __init__(self, e: Expr):
        self.e = e

    def __repr__(self):
        return f"(Assume {self.e})"

    def collect_variables(self):
        return {*self.e.collect_variables()}


class AssertStmt(Stmt):
    def __init__(self, e):
        self.e = e

    def __repr__(self):
        return f"(Assert {self.e})"

    def collect_variables(self):
        return {*self.e.collect_variables()}


class WhileStmt(Stmt):
    def __init__(self, invariant: Expr, cond: Expr, body: Stmt):
        self.invariant = invariant
        self.cond = cond
        self.body = body if body is not None else SkipStmt()

    def __repr__(self):
        return f"(While {self.cond} {self.body})"

    def collect_variables(self):
        return {*self.body.collect_variables()}


class HavocStmt(Stmt):
    def __init__(self, var):
        self.var = var

    def __repr__(self):
        return f"(Havoc {self.var})"

    def collect_variables(self):
        return set()
