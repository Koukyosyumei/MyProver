import ast
import inspect

import z3

from .claim import BinOpExpr, Op, ClaimParser, UnOpExpr
from .hoare import derive_weakest_precondition
from .type import TypeBOOL, TypeINT, resolve_expr_type, resolve_stmt_type, check_and_update_varname2type
from .visitor import ClaimToZ3, PyToClaim


class MyProver:
    def __init__(self):
        self.fname2var_types = {}

    def verify_func(self, func, precond_str, postcond_str):
        code = inspect.getsource(func)
        py_ast = ast.parse(code)
        claim_ast = PyToClaim().visit(py_ast)

        precond_expr = ClaimParser(precond_str).parse_expr()
        postcond_expr = ClaimParser(postcond_str).parse_expr()

        resolve_stmt_type(self.fname2var_types[func.__name__], claim_ast)
        actual, _ = resolve_expr_type(self.fname2var_types[func.__name__], precond_expr)
        check_and_update_varname2type(precond_expr, actual, TypeBOOL, self.fname2var_types[func.__name__])
        actual, _ = resolve_expr_type(self.fname2var_types[func.__name__], postcond_expr)
        check_and_update_varname2type(postcond_expr, actual, TypeBOOL, self.fname2var_types[func.__name__])

        wp, ac = derive_weakest_precondition(claim_ast, postcond_expr, self.fname2var_types[func.__name__])
        conditions_to_be_proved = [BinOpExpr(precond_expr, Op.Implies, wp)] + list(ac)

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
                raise RuntimeError(f"Found a violoated condition: {cond} - {model}")
            solver.pop()

        return True
