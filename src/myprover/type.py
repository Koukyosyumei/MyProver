from abc import ABCMeta

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
    Op,
    QuantificationExpr,
)


class Type(metaclass=ABCMeta):
    pass


class TypeINT(Type):
    def __init__(self) -> None:
        super().__init__()


class TypeBOOL(Type):
    def __init__(self) -> None:
        super().__init__()


class TypeSLICE(Type):
    def __init__(self) -> None:
        super().__init__()


class TypeANY(Type):
    def __init__(self) -> None:
        super().__init__()


class TypeARROW(Type):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2


class TPROD(Type):
    def __init__(self, *types) -> None:
        self.types = tuple(types)


def check_and_update_sigma(expr, actual, expected, sigma):
    if actual == TypeANY and isinstance(expr.e, VarExpr):
        sigma[expr.name] = expected
        return expected
    elif actual == expected:
        # TODO: support subtype
        return actual
    else:
        raise TypeError(f"Expected Type:{expected}, Actual Type:{actual}")


def type_infer_expr(sigma, expr):
    if isinstance(expr, LiteralExpr):
        if type(expr.value) == VBool:
            return TypeBOOL
        elif type(expr.value) == VInt:
            return TypeINT
        else:
            raise NotImplementedError(f"{type(expr.value)} is not supported")
    elif isinstance(expr, VarExpr):
        if sigma is not None and expr.name in sigma:
            return sigma[expr.name]
        else:
            raise NotImplementedError(f"Type of {expr.name} is unkonwn")
    elif isinstance(expr, UnOpExpr):
        if expr.op == Op.Not:
            actual = type_infer_expr(sigma, expr.e)
            expected = TypeBOOL
        elif expr.op == Op.Minus:
            actual = type_infer_expr(sigma, expr.e)
            expected = TypeINT
        return check_and_update_sigma(expr, actual, expected, sigma)

    elif isinstance(expr, BinOpExpr):
        if isinstance(expr.op.value.isArith):
            actual = type_infer_expr(sigma, expr.e1)
            check_and_update_sigma(expr.e1, actual, TypeINT, sigma)
            actual = type_infer_expr(sigma, expr.e2)
            return check_and_update_sigma(expr.e2, actual, TypeINT, sigma)
        elif isinstance(expr.op.value.isComp):
            actual = type_infer_expr(sigma, expr.e1)
            check_and_update_sigma(expr.e1, actual, TypeINT, sigma)
            actual = type_infer_expr(sigma, expr.e2)
            check_and_update_sigma(expr.e2, actual, TypeINT, sigma)
            return TypeBOOL
        elif isinstance(expr.op.value.isBool):
            actual = type_infer_expr(sigma, expr.e1)
            check_and_update_sigma(expr.e1, actual, TypeBOOL, sigma)
            actual = type_infer_expr(sigma, expr.e2)
            return check_and_update_sigma(expr.e2, actual, TypeBOOL, sigma)

    elif isinstance(expr, SliceExpr):
        if expr.lower:
            actual = type_infer_expr(sigma, expr.lower)
            check_and_update_sigma(expr.lower, actual, TypeINT, sigma)
        if expr.upper:
            actual = type_infer_expr(sigma, expr.upper)
            check_and_update_sigma(expr.lower, actual, TypeINT, sigma)
        return TypeSLICE

    elif isinstance(expr, QuantificationExpr):
        sigma[expr.var.name] = TypeANY if expr.var_type is None else expr.var_type
        actual = type_infer_expr(sigma, expr.expr)
        check_and_update_sigma(expr.expr, actual, TypeBOOL, sigma)
        if sigma[expr.var.name] == TypeANY:
            raise TypeError(f"Type of {expr.var} cannot be inffered")
        expr.var_type = sigma[expr.var.name]
        sigma.pop(expr.var.name)
        return TypeBOOL

    else:
        raise NotImplementedError(f"{type(expr)} is not suported")