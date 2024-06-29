import ast
import inspect

import z3

from .claim import BinOpExpr, Op, Parser, UnOpExpr
from .hoare import weakest_precondition
from .type import TypeBOOL, TypeINT, type_infer_expr, type_infer_stmt
from .visitor import ClaimToZ3, PyToClaim


class Verifier:
    def __init__(self):
        self.fname2var_types = {}

    def verify_func(self, func, precond_str, postcond_str):
        code = inspect.getsource(func)
        py_ast = ast.parse(code)
        claim_ast = PyToClaim().visit(py_ast)

        precond_expr = Parser(precond_str).parse_expr()
        postcond_expr = Parser(postcond_str).parse_expr()

        sigma = type_infer_stmt(self.fname2var_types[func.__name__], claim_ast)
        type_infer_expr(sigma, TypeBOOL, precond_expr)
        type_infer_expr(sigma, TypeBOOL, postcond_expr)

        wp, ac = weakest_precondition(claim_ast, postcond_expr, sigma)
        conditions_to_be_proved = [BinOpExpr(precond_expr, Op.Implies, wp)] + ac

        z3_sigma = {}
        for n, t in sigma.items():
            if isinstance(t, TypeINT):
                z3_sigma[n] = z3.Int(n)
            elif isinstance(t, TypeBOOL):
                z3_sigma[n] = z3.Bool(n)

        solver = z3.solver()
        converter = ClaimToZ3(z3_sigma)

        for cond in conditions_to_be_proved:
            solver.push()
            z3_cond = converter.visit(UnOpExpr(Op.Not, cond))
            solver.add(z3_cond)
            result = solver.check()
            if str(result) == "str":
                model = solver.model()
                raise RuntimeError(f"Found a violoated condition: {cond} - {model}")
            solver.pop()
