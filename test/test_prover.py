import inspect
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import myprover as mp
from myprover import assume, invariant, precondition, postcondition, prove


@pytest.fixture
def prover():
    p = mp.MyProver()
    p.sname2var_types = {
        "simple_func": {"x": int, "y": int},
        "complex_func": {
            "x": int,
            "y": int,
            "z": bool,
        },
    }
    return p


def simple_func(x, y):
    result = x + y
    return result


def verify_func(prover, func, precond, postcond, skip_inv=True):
    code = inspect.getsource(func)
    code = code.lstrip()
    return prover.verify(code, func.__name__, precond, postcond, skip_inv)


def test_verify_simple_func_valid(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "result >= 0"
    assert verify_func(prover, simple_func, precond, postcond)


def test_verify_simple_func_invalid(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "result < 0"
    with pytest.raises(mp.VerificationFailureError):
        verify_func(prover, simple_func, precond, postcond)


def complex_func(x, y, z):
    if z:
        result = x - y
    else:
        result = x * y
    return result


def test_verify_complex_func_valid(prover):
    # Note: Currently, we do not support `z == True`.
    precond = "x >= 0 and y >= 0 and (z and True)"
    postcond = "result <= x"
    assert verify_func(prover, complex_func, precond, postcond)


def test_verify_complex_func_invalid(prover):
    # Note: Currently, we do not support `z == False`.
    precond = "x >= 0 and y >= 0 and (not z)"
    postcond = "result < 0"
    with pytest.raises(mp.VerificationFailureError):
        verify_func(prover, complex_func, precond, postcond)


def test_verify_with_no_precond(prover):
    precond = "True"
    postcond = "result == x + y"
    assert verify_func(prover, simple_func, precond, postcond)


def test_verify_with_false_postcond(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "False"
    with pytest.raises(mp.VerificationFailureError):
        verify_func(prover, simple_func, precond, postcond)


def test_verify_with_complex_precond(prover):
    precond = "(x > 0 and y > 0) or (x < 0 and y < 0)"
    postcond = "result != 0"
    assert verify_func(prover, simple_func, precond, postcond)


def test_verify_with_complex_postcond(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "(result == x + y) or (result == x - y)"
    assert verify_func(prover, simple_func, precond, postcond)


def test_verify_with_nested_conditions(prover):
    def nested_func(x, y):
        if x > 0:
            result = x - y
        else:
            result = x + y
        return result

    prover.sname2var_types["nested_func"] = {"x": int, "y": int}
    precond = "x >= 0"
    postcond = "(x > 0 and result == x - y) or (x <= 0 and result == x + y)"
    assert verify_func(prover, nested_func, precond, postcond)


def test_verify_with_bool_var(prover):
    def bool_func(x, y, z):
        if z:
            result = x + y
        else:
            result = x - y
        return result

    prover.sname2var_types["bool_func"] = {
        "x": int,
        "y": int,
        "z": bool,
    }
    precond = "z and True"
    postcond = "result == x + y"
    assert verify_func(prover, bool_func, precond, postcond)


def test_verify_with_unhandled_type(prover):
    def unhandled_func(x):
        return x

    prover.sname2var_types["unhandled_func"] = {"x": int}
    precond = "True"
    postcond = "result == x"
    with pytest.raises(NotImplementedError):
        verify_func(prover, unhandled_func, precond, postcond)


def test_verify_with_assert_stmt(prover):
    def assert_func(x):
        assert x > 0
        return x

    prover.sname2var_types["assert_func"] = {"x": int}
    precond = "x > 0"
    postcond = "x >= 0"
    assert verify_func(prover, assert_func, precond, postcond)


def test_verify_with_assume_stmt(prover):
    def assume_func(x):
        assume("x > 0")
        return x

    prover.sname2var_types["assume_func"] = {"x": int}
    precond = "True"
    postcond = "x >= 1"
    assert verify_func(prover, assume_func, precond, postcond)


def test_while_with_false_invariant(prover):
    def func(x):
        while x > 0:
            invariant("x < 0")
            x = x - 1
        return x

    prover.sname2var_types["func"] = {"x": int}
    precond = "x >= 0"
    postcond = "x == -1"
    with pytest.raises(mp.VerificationFailureError):
        verify_func(prover, func, precond, postcond)


def test_while_with_invariant(prover):
    @precondition("N > 0 and M >= 0")
    @postcondition("M == res * N + m")
    def func(M, N):
        res = 0
        m = M
        while m >= N:
            invariant("M == res * N + m")
            m = m - N
            res = res + 1

    assert prove(
        func,
        {
            "M": int,
            "N": int,
            "res": int,
        },
        False,
    )[0]


def test_while_with_invalid_invariant():
    @precondition("N > 0 and M >= 0")
    @postcondition("M == res * N + m")
    def func(M, N):
        res = 0
        m = M
        while m >= N:
            invariant("M == res * N + m + 1")
            m = m - N
            res = res + 1

    with pytest.raises(mp.InvalidInvariantError):
        prove(
            func,
            {
                "M": int,
                "N": int,
                "res": int,
            },
            False,
        )[0]


def test_while_with_multiple_invariants():
    @precondition("n >= 0")
    @postcondition("r == n * (n + 1) // 2")
    def cumsum(n):
        i = 1
        r = 0
        while i <= n:
            invariant("i <= n + 1")
            invariant("r == (i - 1) * i // 2")
            r = r + i
            i = i + 1

    assert prove(cumsum, {"n": int}, False)[0]
