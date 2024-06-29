from .claim import (
    AssertStmt,
    AssignStmt,
    AssumeStmt,
    BinOpExpr,
    Expr,
    HavocStmt,
    IfStmt,
    LiteralExpr,
    Op,
    QuantificationExpr,
    SeqStmt,
    SkipStmt,
    Stmt,
    UnOpExpr,
    VarExpr,
    VBool,
    WhileStmt,
)


def weakest_precondition(command_stmt: Stmt, post_condition: Expr, var2type):
    """Return the weakest precondition that is necessary to meet the
    post_condition after executing the command_stmt.

    {P} C {Q} <=> P => wp(C, Q)
    """
    if isinstance(command_stmt, SkipStmt):
        # wp(skip, Q <=> Q
        return post_condition, set()
    elif isinstance(command_stmt, AssignStmt):
        # wp(x:=t, Q) = Q[t/x]
        return (
            post_condition.assign_variable(command_stmt.var, command_stmt.expr),
            set(),
        )
    elif isinstance(command_stmt, SeqStmt):
        # wp(C1;C2, Q) <=> wp(C1, wp(C2, Q))
        wp2, ac2 = weakest_precondition(command_stmt.s2, post_condition, var2type)
        wp1, ac1 = weakest_precondition(command_stmt.s1, wp2, var2type)
        return (wp1, ac1.union(ac2))
    elif isinstance(command_stmt, IfStmt):
        # wp(if A then B else C, Q) <=> (A => wp(B, Q)) ^ (!A => wp(C, Q))
        wp1, ac1 = weakest_precondition(command_stmt.lb, post_condition, var2type)
        wp2, ac2 = weakest_precondition(command_stmt.rb, post_condition, var2type)
        cond = BinOpExpr(
            BinOpExpr(command_stmt.cond, Op.Implies, wp1),
            Op.And,
            BinOpExpr(UnOpExpr(Op.Not, command_stmt.cond), Op.Implies, wp2),
        )
        return cond, ac1.union(ac2)
    elif isinstance(command_stmt, WhileStmt):
        if command_stmt is None:
            invariant = LiteralExpr(VBool(True))
        else:
            invariant = command_stmt.invariant
        wp, ac = weakest_precondition(command_stmt.body, invariant, var2type)
        return invariant, ac.union(
            {
                BinOpExpr(
                    BinOpExpr(invariant, Op.And, command_stmt.cond), Op.Implies, wp
                ),
                BinOpExpr(
                    BinOpExpr(invariant, Op.And, UnOpExpr(Op.Not, command_stmt.cond)),
                    Op.Implies,
                    post_condition,
                ),
            }
        )
    elif isinstance(command_stmt, HavocStmt):
        return (
            QuantificationExpr(
                "FORALL",
                VarExpr(command_stmt.var.name + "$0"),
                post_condition.assign_variable(
                    command_stmt.var, VarExpr(command_stmt.var.name + "$0")
                ),
                var2type[command_stmt.var],
            ),
            set(),
        )
    elif isinstance(command_stmt, AssumeStmt):
        return BinOpExpr(command_stmt.e, Op.Implies, post_condition), set()
    elif isinstance(command_stmt, AssertStmt):
        return BinOpExpr(post_condition, command_stmt.e, Op.Implies), set()
