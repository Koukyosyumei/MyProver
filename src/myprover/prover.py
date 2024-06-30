import ast
import inspect

import z3

from .claim import (
    AssertStmt,
    AssignStmt,
    AssumeStmt,
    BinOpExpr,
    ClaimParser,
    CompoundStmt,
    Expr,
    HavocStmt,
    IfElseStmt,
    Op,
    SkipStmt,
    Stmt,
    UnOpExpr,
    WhileStmt,
    LiteralExpr,
    BoolValue,
    VarExpr,
)
from .hoare import derive_weakest_precondition
from .type import (
    TypeBOOL,
    TypeINT,
    check_and_update_varname2type,
    resolve_expr_type,
    resolve_stmt_type,
)
from .visitor import ClaimToZ3, PyToClaim


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


class MyProver:
    """
    A class used to verify the correctness of functions based on preconditions and postconditions.

    Attributes:
        fname2var_types (dict): A dictionary mapping function names to variable types.
    """

    def __init__(self):
        """
        Initializes the MyProver instance with an empty dictionary for function name to variable types mapping.
        """
        self.fname2var_types = {}

    def verify_func(
        self, func, precond_str, postcond_str, skip_verification_of_invariant=True
    ):
        """
        Verifies the correctness of a function based on the given precondition and postcondition strings.

        Args:
            func (function): The function to verify.
            precond_str (str): The precondition string.
            postcond_str (str): The postcondition string.
            skip_verification_of_invariant (bool): If true, skip verifying that the invariant preserves within while-loop.

        Returns:
            bool: True if the function satisfies the precondition and postcondition; otherwise, raises an error.

        Raises:
            RuntimeError: If a violated condition is found during verification.
        """
        code = inspect.getsource(func)
        code = code.lstrip()
        py_ast = ast.parse(code)
        claim_ast = PyToClaim().visit(py_ast)

        precond_expr = ClaimParser(precond_str).parse_expr()
        postcond_expr = ClaimParser(postcond_str).parse_expr()

        resolve_stmt_type(self.fname2var_types[func.__name__], claim_ast)
        actual, _ = resolve_expr_type(self.fname2var_types[func.__name__], precond_expr)
        check_and_update_varname2type(
            precond_expr, actual, TypeBOOL, self.fname2var_types[func.__name__]
        )
        actual, _ = resolve_expr_type(
            self.fname2var_types[func.__name__], postcond_expr
        )
        check_and_update_varname2type(
            postcond_expr, actual, TypeBOOL, self.fname2var_types[func.__name__]
        )

        conditions_for_invariants = []
        if not skip_verification_of_invariant:
            encoded_claim_ast, invariants = encode_while_loop(claim_ast)
            inv_expr = list(invariants)[
                0
            ]  # TODO: Support multiple while-loops within a function
            wpi, aci = derive_weakest_precondition(
                encoded_claim_ast, inv_expr, self.fname2var_types[func.__name__]
            )
            conditions_for_invariants = [
                BinOpExpr(precond_expr, Op.Implies, wpi)
            ] + list(aci)

        wp, ac = derive_weakest_precondition(
            claim_ast, postcond_expr, self.fname2var_types[func.__name__]
        )
        conditions_to_be_proved = (
            conditions_for_invariants
            + [BinOpExpr(precond_expr, Op.Implies, wp)]
            + list(ac)
        )

        z3_env_varname2type = {}
        for n, t in self.fname2var_types[func.__name__].items():
            if t == TypeINT:
                z3_env_varname2type[n] = z3.Int(n)
            elif t == TypeBOOL:
                z3_env_varname2type[n] = z3.Bool(n)

        solver = z3.Solver()
        converter = ClaimToZ3(z3_env_varname2type)

        for cond in conditions_to_be_proved:
            solver.push()
            z3_cond = converter.visit(UnOpExpr(Op.Not, cond))
            solver.add(z3_cond)
            result = solver.check()
            if str(result) == "sat":
                model = solver.model()
                raise RuntimeError(f"Found a violoated condition: {z3_cond} - {model}")
            solver.pop()

        return True
