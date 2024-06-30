import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import myprover as mp


@pytest.fixture
def prover():
    p = mp.MyProver(unroll_while_loop=True)
    p.fname2var_types = {
        "simple_func": {"x": mp.type.TypeINT, "y": mp.type.TypeINT},
        "complex_func": {
            "x": mp.type.TypeINT,
            "y": mp.type.TypeINT,
            "z": mp.type.TypeBOOL,
        },
    }
    return p


def simple_func(x, y):
    result = x + y
    return result


def test_verify_simple_func_valid(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "result >= 0"
    assert prover.verify_func(simple_func, precond, postcond)


def test_verify_simple_func_invalid(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "result < 0"
    with pytest.raises(RuntimeError):
        prover.verify_func(simple_func, precond, postcond)


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
    assert prover.verify_func(complex_func, precond, postcond)


def test_verify_complex_func_invalid(prover):
    # Note: Currently, we do not support `z == False`.
    precond = "x >= 0 and y >= 0 and (not z)"
    postcond = "result < 0"
    with pytest.raises(RuntimeError):
        prover.verify_func(complex_func, precond, postcond)


def test_verify_func_with_no_precond(prover):
    precond = "True"
    postcond = "result == x + y"
    assert prover.verify_func(simple_func, precond, postcond)


def test_verify_func_with_false_postcond(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "False"
    with pytest.raises(RuntimeError):
        prover.verify_func(simple_func, precond, postcond)


def test_verify_func_with_complex_precond(prover):
    precond = "(x > 0 and y > 0) or (x < 0 and y < 0)"
    postcond = "result != 0"
    assert prover.verify_func(simple_func, precond, postcond)


def test_verify_func_with_complex_postcond(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "(result == x + y) or (result == x - y)"
    assert prover.verify_func(simple_func, precond, postcond)


def test_verify_func_with_nested_conditions(prover):
    def nested_func(x, y):
        if x > 0:
            result = x - y
        else:
            result = x + y
        return result

    prover.fname2var_types["nested_func"] = {"x": mp.type.TypeINT, "y": mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "(x > 0 and result == x - y) or (x <= 0 and result == x + y)"
    assert prover.verify_func(nested_func, precond, postcond)


def test_verify_func_with_bool_var(prover):
    def bool_func(x, y, z):
        if z:
            result = x + y
        else:
            result = x - y
        return result

    prover.fname2var_types["bool_func"] = {
        "x": mp.type.TypeINT,
        "y": mp.type.TypeINT,
        "z": mp.type.TypeBOOL,
    }
    precond = "z and True"
    postcond = "result == x + y"
    assert prover.verify_func(bool_func, precond, postcond)


def test_verify_func_with_unhandled_type(prover):
    def unhandled_func(x):
        return x

    prover.fname2var_types["unhandled_func"] = {"x": mp.type.TypeINT}
    precond = "True"
    postcond = "result == x"
    with pytest.raises(NotImplementedError):
        prover.verify_func(unhandled_func, precond, postcond)


def test_verify_func_with_assert_stmt(prover):
    def assert_func(x):
        assert x > 0
        return x

    prover.fname2var_types["assert_func"] = {"x": mp.type.TypeINT}
    precond = "x > 0"
    postcond = "x >= 0"
    assert prover.verify_func(assert_func, precond, postcond)


def test_verify_func_with_assume_stmt(prover):
    def assume_func(x):
        assume("x > 0")
        return x

    prover.fname2var_types["assume_func"] = {"x": mp.type.TypeINT}
    precond = "True"
    postcond = "x >= 1"
    assert prover.verify_func(assume_func, precond, postcond)


def test_simple_while_loop(prover):
    def func(x):
        while x < 5:
            x = x + 1
        return x

    prover.fname2var_types["func"] = {"x": mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "x == 5"
    assert prover.verify_func(func, precond, postcond)


def test_while_with_var_update(prover):
    def func(x):
        y = 0
        while x > 0:
            x = x - 1
            y = y + 1
        return y

    prover.fname2var_types["func"] = {"x": mp.type.TypeINT, "y": mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "y == x"
    assert prover.verify_func(func, precond, postcond)


def test_while_with_nested_loops(prover):
    def func(x, y):
        while x > 0:
            while y > 0:
                y = y - 1
            x = x - 1
        return x, y

    prover.fname2var_types["func"] = {"x": mp.type.TypeINT, "y": mp.type.TypeINT}
    precond = "x >= 0 and y >= 0"
    postcond = "x == 0 and y == 0"
    assert prover.verify_func(func, precond, postcond)


def test_while_with_break(prover):
    def func(x):
        while x < 10:
            if x == 5:
                break
            x = x + 1
        return x

    prover.fname2var_types["func"] = {"x": mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "x == 5"
    assert prover.verify_func(func, precond, postcond)


def test_while_with_continue(prover):
    def func(x, y):
        while x < 10:
            x = x + 1
            if x % 2 == 0:
                continue
            y = y + 1
        return y

    prover.fname2var_types["func"] = {"x": mp.type.TypeINT, "y": mp.type.TypeINT}
    precond = "x >= 0 and y >= 0"
    postcond = "x == 5"
    assert prover.verify_func(func, precond, postcond)

def test_while_with_non_trivial_postcondition(prover):
    def func(x):
        y = 0
        while x > 0:
            y = y + x
            x = x - 1
        return y

    prover.fname2var_types["func"] = {"x": mp.type.TypeINT, "y": mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "y == (x * (x + 1)) // 2"
    assert prover.verify_func(func, precond, postcond)

def test_while_with_false_invariant():
    def func(x):
        while x > 0:
            invariant("x < 0")
            x = x - 1
        return x
    
    prover = mp.MyProver()
    prover.fname2var_types["func"] = {"x": mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "x == -1"
    with pytest.raises(RuntimeError):
        prover.verify_func(func, precond, postcond)
