import ast
import inspect

import z3

from .claim import BinOpExpr, ClaimParser, Op, UnOpExpr
from .exception import InvalidInvariantError, VerificationFailureError
from .hoare import derive_weakest_precondition, encode_while_loop
from .type import check_and_update_varname2type, resolve_expr_type, resolve_stmt_type
from .visitor import ClaimToZ3, PyToClaim


class MyProver:
    """
    A class used to verify the correctness of functions based on preconditions and postconditions.

    Attributes:
        sname2var_types (dict): A dictionary mapping scope names to variable types.
    """

    def __init__(self):
        """
        Initializes the MyProver instance with an empty dictionary for scope name to variable types mapping.
        """
        self.sname2var_types = {}
        self.varname2numhavoced = {}

    def register(self, scope_name: str, var2types: dict[str, type]) -> None:
        self.sname2var_types[scope_name] = var2types

    def verify(
        self,
        code_str: str,
        scope_name: str,
        precond_str: str,
        postcond_str: str,
        skip_verification_of_invariant: bool = True,
    ) -> bool:
        """
        Verifies the correctness of a function based on the given precondition and postcondition strings.

        Args:
            code_str (str): The code string to verify.
            scope_name (str): The name of the scope, such as a name of a function.
            precond_str (str): The precondition string.
            postcond_str (str): The postcondition string.
            skip_verification_of_invariant (bool): If true, skip verifying that the invariant preserves within while-loop.

        Returns:
            bool: True if the function satisfies the precondition and postcondition; otherwise, raises an error.

        Raises:
            RuntimeError: If a violated condition is found during verification.
        """
        py_ast = ast.parse(code_str)
        claim_ast = PyToClaim().visit(py_ast)

        precond_expr = ClaimParser(precond_str).parse_expr()
        postcond_expr = ClaimParser(postcond_str).parse_expr()

        resolve_stmt_type(self.sname2var_types[scope_name], claim_ast)
        actual, _ = resolve_expr_type(self.sname2var_types[scope_name], precond_expr)
        check_and_update_varname2type(
            precond_expr, actual, bool, self.sname2var_types[scope_name]
        )
        actual, _ = resolve_expr_type(self.sname2var_types[scope_name], postcond_expr)
        check_and_update_varname2type(
            postcond_expr, actual, bool, self.sname2var_types[scope_name]
        )

        conditions_for_invariants = []
        if not skip_verification_of_invariant:
            encoded_claim_ast, invariants = encode_while_loop(claim_ast, self.varname2numhavoced)
            inv_expr = list(invariants)[
                0
            ]  # TODO: Support multiple while-loops within a function
            wpi, aci = derive_weakest_precondition(
                encoded_claim_ast, inv_expr, self.sname2var_types[scope_name]
            )
            conditions_for_invariants = [
                BinOpExpr(precond_expr, Op.Implies, wpi)
            ] + list(aci)
            for c in conditions_for_invariants:
                c._is_expr_to_verify_invriant = True

        wp, ac = derive_weakest_precondition(
            claim_ast, postcond_expr, self.sname2var_types[scope_name]
        )
        conditions_to_be_proved = (
            conditions_for_invariants
            + [BinOpExpr(precond_expr, Op.Implies, wp)]
            + list(ac)
        )

        z3_env_varname2type = {}
        for n, t in self.sname2var_types[scope_name].items():
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
                if cond._is_expr_to_verify_invriant:
                    raise InvalidInvariantError(
                        f"Invalid invariant is specified: {z3_cond} - {model}"
                    )
                else:
                    raise VerificationFailureError(
                        f"Found a violoated condition: {z3_cond} - {model}"
                    )
            solver.pop()

        return True


def prove(func, varname2types=None, skip_inv=True):
    precond = getattr(func, "_precondition", "True")
    postcond = getattr(func, "_postcondition", "True")
    code = inspect.getsource(func)
    code = ("\n".join(code.split("\n")[2:])).lstrip()
    prover = MyProver()
    prover.register(func.__name__, varname2types)
    return prover.verify(code, func.__name__, precond, postcond, skip_inv), prover
