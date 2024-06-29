import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import myprover as mp

@pytest.fixture
def prover():
    p = mp.MyProver()
    p.fname2var_types = {
        'simple_func': {'x': mp.type.TypeINT, 'y': mp.type.TypeINT},
        'complex_func': {'x': mp.type.TypeINT, 'y': mp.type.TypeINT, 'z': mp.type.TypeBOOL}
    }
    return p

def simple_func(x, y):
    result = x + y
    return result

def complex_func(x, y, z):
    if z:
        result = x - y
    else:
        result = x * y
    return result

def test_verify_simple_func_valid(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "result >= 0"
    assert prover.verify_func(simple_func, precond, postcond)

"""
def test_verify_simple_func_invalid(prover):
    precond = "x >= 0 and y >= 0"
    postcond = "result < 0"
    with pytest.raises(RuntimeError):
        prover.verify_func(simple_func, precond, postcond)

def test_verify_complex_func_valid(prover):
    precond = "x >= 0 and y >= 0 and z == True"
    postcond = "result <= x"
    assert prover.verify_func(complex_func, precond, postcond)

def test_verify_complex_func_invalid(prover):
    precond = "x >= 0 and y >= 0 and z == False"
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
            return x - y
        else:
            return x + y
    
    prover.fname2var_types['nested_func'] = {'x': mp.type.TypeINT, 'y': mp.type.TypeINT}
    precond = "x >= 0"
    postcond = "(x > 0 and result == x - y) or (x <= 0 and result == x + y)"
    assert prover.verify_func(nested_func, precond, postcond)

def test_verify_func_with_bool_var(prover):
    def bool_func(x, y, z):
        if z:
            return x + y
        else:
            return x - y
    
    prover.fname2var_types['bool_func'] = {'x': mp.type.TypeINT, 'y': mp.type.TypeINT, 'z': mp.type.TypeBOOL}
    precond = "z == True"
    postcond = "result == x + y"
    assert prover.verify_func(bool_func, precond, postcond)

def test_verify_func_with_unhandled_type(prover):
    def unhandled_func(x):
        return x
    
    prover.fname2var_types['unhandled_func'] = {'x': mp.type.TypeINT}
    precond = "True"
    postcond = "result == x"
    with pytest.raises(NotImplementedError):
        prover.verify_func(unhandled_func, precond, postcond)

def test_verify_func_with_assert_stmt(prover):
    def assert_func(x):
        assert x > 0
        return x
    
    prover.fname2var_types['assert_func'] = {'x': mp.type.TypeINT}
    precond = "x > 0"
    postcond = "result == x"
    assert prover.verify_func(assert_func, precond, postcond)
"""

"""
def test_verify_func_with_assume_stmt(prover):
    def assume_func(x):
        assume x > 0
        return x
    
    prover.fname2var_types['assume_func'] = {'x': mp.type.TypeINT}
    precond = "True"
    postcond = "result == x"
    assert prover.verify_func(assume_func, precond, postcond)
"""