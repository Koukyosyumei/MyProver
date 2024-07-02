from abc import ABCMeta

from .claim import (
    AssertStmt,
    AssignStmt,
    AssumeStmt,
    BinOpExpr,
    BoolValue,
    CompoundStmt,
    HavocStmt,
    IfElseStmt,
    IntValue,
    LiteralExpr,
    Op,
    QuantificationExpr,
    SkipStmt,
    SliceExpr,
    Stmt,
    UnOpExpr,
    VarExpr,
    WhileStmt,
    Expr,
)


def check_and_update_varname2type(
    expr: Expr, actual: type, expected: type, env_varname2type: dict[str, type]
) -> tuple[type, bool]:
    """Check and update the type environment env_varname2type based on type checking rules.

    Args:
        expr: The expression to check.
        actual (Type): The actual type inferred for the expression.
        expected (Type): The expected type for the expression.
        env_varname2type (dict): The type environment dictionary.

    Returns:
        tuple: A tuple containing the updated type and a boolean indicating if env_varname2type was updated.

    Raises:
        TypeError: If there is a type mismatch between actual and expected types.
    """
    if actual == None and isinstance(expr.e, VarExpr):
        env_varname2type[expr.name] = expected
        return expected, True
    elif actual == expected:
        # TODO: support subtype
        return actual, False
    else:
        raise TypeError(f"Expected Type:{expected}, Actual Type:{actual}")


def resolve_expr_type(
    env_varname2type: dict[str, type], expr: Expr
) -> tuple[type, bool]:
    """Resolve the type of an expression recursively using type inference.

    Args:
        env_varname2type (dict): The type environment dictionary.
        expr (Expr): The expression to resolve.

    Returns:
        tuple: A tuple containing the resolved type and a boolean indicating if the type environment env_varname2type was updated.

    Raises:
        NotImplementedError: If the expression type is not supported.
    """
    if isinstance(expr, LiteralExpr):
        if type(expr.value) == BoolValue:
            return bool, False
        elif type(expr.value) == IntValue:
            return int, False
        else:
            raise NotImplementedError(f"{type(expr.value)} is not supported")
    elif isinstance(expr, VarExpr):
        if env_varname2type is not None and expr.name in env_varname2type:
            return env_varname2type[expr.name], False
        else:
            raise NotImplementedError(f"Type of the variable `{expr.name}` is unkonwn")
    elif isinstance(expr, UnOpExpr):
        if expr.op == Op.Not:
            actual, isupdated_e = resolve_expr_type(env_varname2type, expr.e)
            expected = bool
        elif expr.op == Op.Minus:
            actual, isupdated_e = resolve_expr_type(env_varname2type, expr.e)
            expected = int
        type_expr, isupdated_expr = check_and_update_varname2type(
            expr, actual, expected, env_varname2type
        )
        return type_expr, isupdated_e or isupdated_expr

    elif isinstance(expr, BinOpExpr):
        if expr.op.value.isArith:
            actual, isupdated_e1_1 = resolve_expr_type(env_varname2type, expr.e1)
            _, isupdated_e1_2 = check_and_update_varname2type(
                expr.e1, actual, int, env_varname2type
            )
            actual, isupdated_e2_1 = resolve_expr_type(env_varname2type, expr.e2)
            type_e2, isupdated_e2_2 = check_and_update_varname2type(
                expr.e2, actual, int, env_varname2type
            )
            return (
                type_e2,
                isupdated_e1_1 or isupdated_e1_2 or isupdated_e2_1 or isupdated_e2_2,
            )
        elif expr.op.value.isComp:
            actual, isupdated_e1_1 = resolve_expr_type(env_varname2type, expr.e1)
            _, isupdated_e1_2 = check_and_update_varname2type(
                expr.e1, actual, int, env_varname2type
            )
            actual, isupdated_e2_1 = resolve_expr_type(env_varname2type, expr.e2)
            _, isupdated_e2_2 = check_and_update_varname2type(
                expr.e2, actual, int, env_varname2type
            )
            return (
                bool,
                isupdated_e1_1 or isupdated_e1_2 or isupdated_e2_1 or isupdated_e2_2,
            )
        elif expr.op.value.isBool:
            actual, isupdated_e1_1 = resolve_expr_type(env_varname2type, expr.e1)
            _, isupdated_e1_2 = check_and_update_varname2type(
                expr.e1, actual, bool, env_varname2type
            )
            actual, isupdated_e2_1 = resolve_expr_type(env_varname2type, expr.e2)
            type_e2, isupdated_e2_2 = check_and_update_varname2type(
                expr.e2, actual, bool, env_varname2type
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
            actual, isupdated_lower_1_1 = resolve_expr_type(
                env_varname2type, expr.lower
            )
            _, isupdated_lower_1_2 = check_and_update_varname2type(
                expr.lower, actual, int, env_varname2type
            )
        if expr.upper:
            actual, isupdated_higher_1_1 = resolve_expr_type(
                env_varname2type, expr.upper
            )
            _, isupdated_higher_1_2 = check_and_update_varname2type(
                expr.lower, actual, int, env_varname2type
            )
        return (
            None,
            isupdated_lower_1_1
            or isupdated_lower_1_2
            or isupdated_higher_1_1
            or isupdated_higher_1_2,
        )

    elif isinstance(expr, QuantificationExpr):
        env_varname2type[expr.var.name] = (
            None if expr.var_type is None else expr.var_type
        )
        actual, _ = resolve_expr_type(env_varname2type, expr.expr)
        check_and_update_varname2type(expr.expr, actual, bool, env_varname2type)
        if env_varname2type[expr.var.name] == None:
            raise TypeError(
                f"Type of the variable `{expr.var.name}` cannot be inffered"
            )
        expr.var_type = env_varname2type[expr.var.name]
        env_varname2type.pop(expr.var.name)
        return bool, True

    else:
        raise NotImplementedError(f"{type(expr)} is not suported")


def resolve_stmt_type(env_varname2type: dict[str, type], stmt: Stmt) -> bool:
    """Resolve the type of a statement using type inference.

    Args:
        env_varname2type (dict): The type environment dictionary.
        stmt (Stmt): The statement to resolve.

    Returns:
        bool: A boolean indicating if the type environment env_varname2type was updated.

    Raises:
        NotImplementedError: If the statement type is not supported.
    """
    if isinstance(stmt, SkipStmt):
        return False
    elif isinstance(stmt, CompoundStmt):
        isupdated_s1 = resolve_stmt_type(env_varname2type, stmt.s1)
        isupdated_s2 = resolve_stmt_type(env_varname2type, stmt.s2)
        return isupdated_s1 or isupdated_s2
    elif isinstance(stmt, AssignStmt):
        type_of_expr, isupdated = resolve_expr_type(env_varname2type, stmt.expr)
        if stmt.var.name not in env_varname2type:
            env_varname2type[stmt.var.name] = type_of_expr
            return True
        else:
            if env_varname2type[stmt.var.name] == None:
                env_varname2type[stmt.var.name] = type_of_expr
                return True
            elif env_varname2type[stmt.var.name] != type_of_expr:
                raise TypeError(f"Type Mismatch of {stmt.var}")
            else:
                return isupdated
    elif isinstance(stmt, IfElseStmt):
        actual, isupdated_cond1 = resolve_expr_type(env_varname2type, stmt.cond)
        _, isupdated_cond2 = check_and_update_varname2type(
            stmt.cond, actual, bool, env_varname2type
        )
        isupdated_then = resolve_stmt_type(env_varname2type, stmt.then_branch)
        isupdated_else = resolve_stmt_type(env_varname2type, stmt.else_branch)
        return isupdated_cond1 or isupdated_cond2 or isupdated_then or isupdated_else
    elif isinstance(stmt, AssertStmt):
        actual, isupdated_1 = resolve_expr_type(env_varname2type, stmt.e)
        _, isupdated_2 = check_and_update_varname2type(
            stmt.e, actual, bool, env_varname2type
        )
        return isupdated_1 or isupdated_2
    elif isinstance(stmt, AssumeStmt):
        actual, isupdated_1 = resolve_expr_type(env_varname2type, stmt.e)
        _, isupdated_2 = check_and_update_varname2type(
            stmt.e, actual, bool, env_varname2type
        )
        return isupdated_1 or isupdated_2
    elif isinstance(stmt, WhileStmt):
        actual, isupdated = resolve_expr_type(env_varname2type, stmt.cond)
        _, tmp_isupdated = check_and_update_varname2type(
            stmt.cond, actual, bool, env_varname2type
        )
        isupdated = isupdated or tmp_isupdated
        actual, tmp_isupdated_1 = resolve_expr_type(env_varname2type, stmt.invariant)
        _, tmp_isupdated_2 = check_and_update_varname2type(
            stmt.invariant, actual, bool, env_varname2type
        )
        isupdated = isupdated or tmp_isupdated_1 or tmp_isupdated_2
        _isupdated = resolve_stmt_type(env_varname2type, stmt.body)
        return isupdated or _isupdated
    elif isinstance(stmt, HavocStmt):
        return False
    raise NotImplementedError(f"{type(stmt)} is not supported")
