import ast
import inspect

import z3

from .claim import (
    BinOpExpr,
    ClaimParser,
    Op,
    UnOpExpr
)
from .hoare import derive_weakest_precondition, encode_while_loop
from .type import (
    check_and_update_varname2type,
    resolve_expr_type,
    resolve_stmt_type,
)
from .visitor import ClaimToZ3, PyToClaim


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
            precond_expr, actual, bool, self.fname2var_types[func.__name__]
        )
        actual, _ = resolve_expr_type(
            self.fname2var_types[func.__name__], postcond_expr
        )
        check_and_update_varname2type(
            postcond_expr, actual, bool, self.fname2var_types[func.__name__]
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
            if t == int:
                z3_env_varname2type[n] = z3.Int(n)
            elif t == bool:
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
