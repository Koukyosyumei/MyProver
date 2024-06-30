import copy

from .claim import (
    AssertStmt,
    AssignStmt,
    AssumeStmt,
    BinOpExpr,
    BoolValue,
    CompoundStmt,
    Expr,
    HavocStmt,
    IfElseStmt,
    LiteralExpr,
    Op,
    QuantificationExpr,
    SkipStmt,
    Stmt,
    UnOpExpr,
    VarExpr,
    WhileStmt,
)


def derive_weakest_precondition(command_stmt: Stmt, post_condition: Expr, var2type):
    """Computes the weakest precondition necessary to meet the post_condition after executing the command_stmt.

    Given a command statement `command_stmt` and a post-condition `post_condition`, this function calculates
    the weakest precondition (wp) such that if the wp holds before the execution of `command_stmt`,
    then `post_condition` will hold after its execution. This is based on the Hoare logic formulation:

    {P} C {Q} <=> P => wp(C, Q)

    Args:
        command_stmt (Stmt): The command statement whose weakest precondition is to be calculated.
        post_condition (Expr): The post-condition expression that should hold after the execution of the command.
        var2type (dict): A dictionary mapping variable names to their types.

    Returns:
        tuple: A tuple containing the weakest precondition expression and a set of auxiliary conditions.

    Raises:
        TypeError: If the type of command_stmt is not recognized or not supported.
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
    elif isinstance(command_stmt, CompoundStmt):
        # wp(C1;C2, Q) <=> wp(C1, wp(C2, Q))
        wp2, ac2 = derive_weakest_precondition(
            command_stmt.s2, post_condition, var2type
        )
        wp1, ac1 = derive_weakest_precondition(command_stmt.s1, wp2, var2type)
        return wp1, ac1.union(ac2)
    elif isinstance(command_stmt, IfElseStmt):
        # wp(if A then B else C, Q) <=> (A => wp(B, Q)) ^ (!A => wp(C, Q))
        wp1, ac1 = derive_weakest_precondition(
            command_stmt.then_branch, post_condition, var2type
        )
        wp2, ac2 = derive_weakest_precondition(
            command_stmt.else_branch, post_condition, var2type
        )
        cond = BinOpExpr(
            BinOpExpr(command_stmt.cond, Op.Implies, wp1),
            Op.And,
            BinOpExpr(UnOpExpr(Op.Not, command_stmt.cond), Op.Implies, wp2),
        )
        return cond, ac1.union(ac2)
    elif isinstance(command_stmt, WhileStmt):
        if command_stmt.invariant is None:
            invariant = LiteralExpr(BoolValue(True))
        else:
            invariant = command_stmt.invariant

        wp, ac = derive_weakest_precondition(command_stmt.body, invariant, var2type)

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
                VarExpr(command_stmt.var_name + "$0"),
                post_condition.assign_variable(
                    VarExpr(command_stmt.var_name),
                    VarExpr(command_stmt.var_name + "$0"),
                ),
                var2type[command_stmt.var_name],
            ),
            set(),
        )
    elif isinstance(command_stmt, AssumeStmt):
        return BinOpExpr(command_stmt.e, Op.Implies, post_condition), set()
    elif isinstance(command_stmt, AssertStmt):
        return BinOpExpr(post_condition, Op.Implies, command_stmt.e), set()
    
    
def encode_while_loop(stmt: Stmt):
    if (
        isinstance(stmt, AssignStmt)
        or isinstance(stmt, AssertStmt)
        or isinstance(stmt, AssumeStmt)
        or isinstance(stmt, HavocStmt)
        or isinstance(stmt, SkipStmt)
    ):
        return stmt, set()
    elif isinstance(stmt, CompoundStmt):
        s1, iv1 = encode_while_loop(stmt.s1.clone())
        s2, iv2 = encode_while_loop(stmt.s2.clone())
        return CompoundStmt(s1, s2), {*iv1, *iv2}
    elif isinstance(stmt, IfElseStmt):
        st, ivt = encode_while_loop(stmt.then_stmt.clone())
        se, ive = encode_while_loop(stmt.else_stmt.clone())
        return IfElseStmt(stmt.cond_expr, st, se), {*ivt, *ive}
    elif isinstance(stmt, WhileStmt):
        # https://courses.cs.washington.edu/courses/cse507/19wi/doc/L13.pdf
        # https://ethz.ch/content/dam/ethz/special-interest/infk/chair-program-method/pm/documents/Education/Courses/SS2022/PV/slides/04-loops-procedures-solutions.pdf
        # we need to prove that the given invariant condition perserves within the loop.
        # ----------------
        # // prior code
        # assert invariant (check that invariant is satisfied before entering the loop)
        # havoc loop targets (havo the variables that may change within the loop)
        # assume invariant (assume that the (havoced) invariant is satisfied before entering the loop
        # if (cond)
        #    body
        #    assert invariant (check that invariant is satisfied after the loop)
        #    assume false (kill this branch to prevent it from going further since it is originally a loop)
        # else
        #    skip
        # {invariant} (post-condition)
        # ----------------
        
        loop_target_varnames = stmt.body.collect_assigned_varnames()
        havocs = list(map(HavocStmt, loop_target_varnames))
        after_havoc_stmts = [
            AssumeStmt(stmt.invariant.clone()),
            IfElseStmt(
                stmt.cond,
                CompoundStmt(
                    CompoundStmt(stmt.body, AssertStmt(stmt.invariant.clone())),
                    AssumeStmt(LiteralExpr(BoolValue(False))),
                ),
                SkipStmt(),
            ),
        ]
        for i in range(len(after_havoc_stmts)):
            for h in havocs:
                after_havoc_stmts[i] = after_havoc_stmts[i].assign_variable(
                    VarExpr(h.var_name), VarExpr(h.var_name + "$0")
                )

        encoded_loop_items = [
            AssertStmt(stmt.invariant.clone()),
            *havocs,
        ] + after_havoc_stmts
        s = CompoundStmt(encoded_loop_items[0], encoded_loop_items[1])
        for i in encoded_loop_items[2:]:
            s = CompoundStmt(s.s1, CompoundStmt(s.s2, i))

        havoced_invariant = stmt.invariant.clone()
        for h in havocs:
            havoced_invariant = havoced_invariant.assign_variable(
                VarExpr(h.var_name), VarExpr(h.var_name + "$0")
            )

        return s, {havoced_invariant}
    else:
        raise NotImplementedError(f"{type(stmt)} is not supported")
