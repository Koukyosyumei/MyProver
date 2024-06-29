from abc import ABCMeta

from .claim import (
    AssertStmt,
    AssignStmt,
    AssumeStmt,
    BinOpExpr,
    HavocStmt,
    IfStmt,
    LiteralExpr,
    Op,
    ClaimParser,
    QuantificationExpr,
    SeqStmt,
    SkipStmt,
    SliceExpr,
    SubscriptExpr,
    UnOpExpr,
    VarExpr,
    VBool,
    VInt,
    WhileStmt,
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
        return expected, True
    elif actual == expected:
        # TODO: support subtype
        return actual, False
    else:
        raise TypeError(f"Expected Type:{expected}, Actual Type:{actual}")


def type_infer_expr(sigma, expr):
    if isinstance(expr, LiteralExpr):
        if type(expr.value) == VBool:
            return TypeBOOL, False
        elif type(expr.value) == VInt:
            return TypeINT, False
        else:
            raise NotImplementedError(f"{type(expr.value)} is not supported")
    elif isinstance(expr, VarExpr):
        if sigma is not None and expr.name in sigma:
            return sigma[expr.name], False
        else:
            raise NotImplementedError(f"Type of {expr.name} is unkonwn")
    elif isinstance(expr, UnOpExpr):
        if expr.op == Op.Not:
            actual, isupdated_e = type_infer_expr(sigma, expr.e)
            expected = TypeBOOL
        elif expr.op == Op.Minus:
            actual, isupdated_e = type_infer_expr(sigma, expr.e)
            expected = TypeINT
        type_expr, isupdated_expr = check_and_update_sigma(
            expr, actual, expected, sigma
        )
        return type_expr, isupdated_e or isupdated_expr

    elif isinstance(expr, BinOpExpr):
        if expr.op.value.isArith:
            actual, isupdated_e1_1 = type_infer_expr(sigma, expr.e1)
            _, isupdated_e1_2 = check_and_update_sigma(expr.e1, actual, TypeINT, sigma)
            actual, isupdated_e2_1 = type_infer_expr(sigma, expr.e2)
            type_e2, isupdated_e2_2 = check_and_update_sigma(
                expr.e2, actual, TypeINT, sigma
            )
            return (
                type_e2,
                isupdated_e1_1 or isupdated_e1_2 or isupdated_e2_1 or isupdated_e2_2,
            )
        elif expr.op.value.isComp:
            actual, isupdated_e1_1 = type_infer_expr(sigma, expr.e1)
            _, isupdated_e1_2 = check_and_update_sigma(expr.e1, actual, TypeINT, sigma)
            actual, isupdated_e2_1 = type_infer_expr(sigma, expr.e2)
            _, isupdated_e2_2 = check_and_update_sigma(expr.e2, actual, TypeINT, sigma)
            return (
                TypeBOOL,
                isupdated_e1_1 or isupdated_e1_2 or isupdated_e2_1 or isupdated_e2_2,
            )
        elif expr.op.value.isBool:
            actual, isupdated_e1_1 = type_infer_expr(sigma, expr.e1)
            _, isupdated_e1_2 = check_and_update_sigma(expr.e1, actual, TypeBOOL, sigma)
            actual, isupdated_e2_1 = type_infer_expr(sigma, expr.e2)
            type_e2, isupdated_e2_2 = check_and_update_sigma(
                expr.e2, actual, TypeBOOL, sigma
            )
            return (
                type_e2,
                isupdated_e1_1 or isupdated_e1_2 or isupdated_e2_1 or isupdated_e2_2,
            )

    elif isinstance(expr, SliceExpr):
        (
            isupdated_lower_1_1,
            isupdated_lower_1_2,
            isupdated_higher_1_1,
            isupdated_higher_1_1,
        ) = (False, False, False, False)
        if expr.lower:
            actual, isupdated_lower_1_1 = type_infer_expr(sigma, expr.lower)
            _, isupdated_lower_1_2 = check_and_update_sigma(
                expr.lower, actual, TypeINT, sigma
            )
        if expr.upper:
            actual, isupdated_higher_1_1 = type_infer_expr(sigma, expr.upper)
            _, isupdated_higher_1_2 = check_and_update_sigma(
                expr.lower, actual, TypeINT, sigma
            )
        return (
            TypeSLICE,
            isupdated_lower_1_1
            or isupdated_lower_1_2
            or isupdated_higher_1_1
            or isupdated_higher_1_2,
        )

    elif isinstance(expr, QuantificationExpr):
        sigma[expr.var.name] = TypeANY if expr.var_type is None else expr.var_type
        actual, _ = type_infer_expr(sigma, expr.expr)
        check_and_update_sigma(expr.expr, actual, TypeBOOL, sigma)
        if sigma[expr.var.name] == TypeANY:
            raise TypeError(f"Type of {expr.var} cannot be inffered")
        expr.var_type = sigma[expr.var.name]
        sigma.pop(expr.var.name)
        return TypeBOOL, True

    else:
        raise NotImplementedError(f"{type(expr)} is not suported")


def type_infer_stmt(sigma, stmt):
    if isinstance(stmt, SkipStmt):
        return False
    elif isinstance(stmt, SeqStmt):
        isupdated_s1 = type_infer_stmt(sigma, stmt.s1)
        isupdated_s2 = type_infer_stmt(sigma, stmt.s2)
        return isupdated_s1 or isupdated_s2
    elif isinstance(stmt, AssignStmt):
        type_of_expr, isupdated = type_infer_expr(sigma, stmt.expr)
        if stmt.var.name not in sigma:
            sigma[stmt.var.name] = type_of_expr
            return True
        else:
            if sigma[stmt.var.name] == TypeANY:
                sigma[stmt.var.name] = type_of_expr
                return True
            elif sigma[stmt.var.name] != type_of_expr:
                raise TypeError(f"Type Mismatch of {stmt.var}")
            else:
                return isupdated
    elif isinstance(stmt, IfStmt):
        actual, isupdated_cond1 = type_infer_expr(sigma, stmt.cond)
        _, isupdated_cond2 = check_and_update_sigma(stmt.cond, actual, TypeBOOL, sigma)
        isupdated_lb = type_infer_stmt(sigma, stmt.lb)
        isupdated_rb = type_infer_stmt(sigma, stmt.rb)
        return isupdated_cond1 or isupdated_cond2 or isupdated_lb or isupdated_rb
    elif isinstance(stmt, AssertStmt):
        actual, isupdated_1 = type_infer_expr(sigma, stmt.e)
        _, isupdated_2 = check_and_update_sigma(stmt.e, actual, TypeBOOL, sigma)
        return isupdated_1 or isupdated_2
    elif isinstance(stmt, WhileStmt):
        actual, isupdated = type_infer_expr(sigma, stmt.cond)
        _, tmp_isupdated = check_and_update_sigma(stmt.cond, actual, TypeBOOL, sigma)
        isupdated = isupdated or tmp_isupdated
        actual, tmp_isupdated_1 = type_infer_expr(sigma, TypeBOOL, stmt.invariant)
        _, tmp_isupdated_2 = check_and_update_sigma(stmt.invariant, actual, TypeBOOL, sigma)
        isupdated = isupdated or tmp_isupdated_1 or tmp_isupdated_2
        _isupdated = type_infer_stmt(sigma, stmt.body)
        return isupdated or _isupdated
    elif isinstance(stmt, HavocStmt):
        return False
    raise NotImplementedError(f"{type(stmt)} is not supported")
