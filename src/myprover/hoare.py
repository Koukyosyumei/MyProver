from .stmt import (
    Stmt,
    SkipStmt,
    AssertStmt,
    AssignStmt,
    IfStmt,
    WhileStmt,
    HavocStmt,
    SeqStmt,
    AssumeStmt,
)
from .ast import (
    Expr,
    BinOpExpr,
    UnOpExpr,
    Op,
    LiteralExpr,
    VBool,
    QuantificationExpr,
    VarExpr,
)


def weakest_precondition(command_stmt: Stmt, post_condition: Expr, var2type):
    """Return the weakest precondition that is necessary to meet the
    post_condition after executing the command_stmt.

    {P} C {Q} <=> P => wp(C, Q)
    """
    if type(command_stmt) == SkipStmt:
        # wp(skip, Q <=> Q
        return post_condition, set()
    elif type(command_stmt) == AssignStmt:
        # wp(x:=t, Q) = Q[t/x]
        return post_condition.substitute(command_stmt.var, command_stmt.expr), set()
    elif type(command_stmt) == SeqStmt:
        # wp(C1;C2, Q) <=> wp(C1, wp(C2, Q))
        wp2, c2 = weakest_precondition(command_stmt.s2, post_condition, var2type)
        wp1, c1 = weakest_precondition(command_stmt.s1, wp2, var2type)
        return (wp1, c1.union(c2))
    elif type(command_stmt) == IfStmt:
        # wp(if A then B else C, Q) <=> (A => wp(B, Q)) ^ (!A => wp(C, Q))
        wp1, c1 = weakest_precondition(command_stmt.lb, post_condition, var2type)
        wp2, c2 = weakest_precondition(command_stmt.rb, post_condition, var2type)
        cond = BinOpExpr(
            BinOpExpr(command_stmt.cond, Op.Implies, wp1),
            Op.And,
            BinOpExpr(UnOpExpr(Op.Not, command_stmt.cond), Op.Implies, wp2),
        )
        return cond, c1.union(c2)
    elif type(command_stmt) == WhileStmt:
        if command_stmt is None:
            invariants = LiteralExpr(VBool(True))
        else:
            invariants = command_stmt.invariants
        wp, c = weakest_precondition(command_stmt.body, invariants, var2type)
        return invariants, c.union(
            {
                BinOpExpr(
                    BinOpExpr(invariants, Op.And, command_stmt.cond), Op.Implies, wp
                ),
                BinOpExpr(
                    BinOpExpr(invariants, Op.And, UnOpExpr(Op.Not, command_stmt.cond)),
                    Op.Implies,
                    post_condition,
                ),
            }
        )
    elif type(command_stmt) == HavocStmt:
        return (
            QuantificationExpr(
                "FORALL",
                VarExpr(command_stmt.var.name + "$0"),
                post_condition.substitute(
                    command_stmt.var, VarExpr(command_stmt.var.name + "$0")
                ),
                var2type[command_stmt.var],
            ),
            set(),
        )
    elif type(command_stmt) == AssumeStmt:
        return BinOpExpr(command_stmt.e, Op.Implies, post_condition), set()
    elif type(command_stmt) == AssertStmt:
        return BinOpExpr(post_condition, command_stmt.e, Op.Implies), set()
