import ast
import os
import sys

import pytest
import z3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_py2claim():
    import myprover as mp

    source = "a = 1 + 1\nb = 5 * 2"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (Assign (Var a) (BinOp (Literal IntValue 1) Op.Add (Literal IntValue 1))) (Assign (Var b) (BinOp (Literal IntValue 5) Op.Mult (Literal IntValue 2))))"
    )

    source = "x <= 2\nx == 2"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (BinOp (Var x) Op.Le (Literal IntValue 2)) (BinOp (Var x) Op.Eq (Literal IntValue 2)))"
    )

    source = "if x == 1:\n    y = 30 % 2\nelse:\n    z = 2"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (If (BinOp (Var x) Op.Eq (Literal IntValue 1)) (Seq (Assign (Var y) (BinOp (Literal IntValue 30) Op.Mod (Literal IntValue 2))) (Skip)) (Seq (Assign (Var z) (Literal IntValue 2)) (Skip))) (Skip))"
    )

    source = "x = y[1:]\nx = y[:1]\nx = y[1:3]"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (Seq (Assign (Var x) (Subscript (Var y) (Slice (Literal IntValue 1) -> None))) (Assign (Var x) (Subscript (Var y) (Slice (Literal IntValue 0) -> (Literal IntValue 1))))) (Assign (Var x) (Subscript (Var y) (Slice (Literal IntValue 1) -> (Literal IntValue 3)))))"
    )

    source = "def f(n):\n    while x > 0:\n        x = x - 1"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (Seq (Seq (Assert (Literal BoolValue True)) (Havoc x)) (Assume (Literal BoolValue True))) (If (BinOp (Var x) Op.Gt (Literal IntValue 0)) (Seq (Seq (Seq (Assign (Var x) (BinOp (Var x) Op.Minus (Literal IntValue 1))) (Skip)) (Assert (Literal BoolValue True))) (Assume (Literal BoolValue False))) (Skip)))"
    )


@pytest.fixture
def name_dict():
    return {"x": z3.Int("x"), "y": z3.Int("y"), "z": z3.Bool("z")}


@pytest.fixture
def claim_to_z3(name_dict):
    import myprover as mp

    return mp.ClaimToZ3(name_dict)


def test_claim2z3_simple(claim_to_z3, name_dict):
    import myprover as mp

    expr = mp.claim.LiteralExpr(mp.claim.IntValue(5))
    assert claim_to_z3.visit(expr) == 5

    expr = mp.claim.LiteralExpr(mp.claim.BoolValue(True))
    assert claim_to_z3.visit(expr) == True

    expr = mp.claim.VarExpr("x")
    assert claim_to_z3.visit(expr) == name_dict["x"]


def test_claim2z3_operations(claim_to_z3, name_dict):
    import myprover as mp

    expr = mp.claim.BinOpExpr(
        mp.claim.VarExpr("x"), mp.claim.Op.Add, mp.claim.VarExpr("y")
    )
    result = claim_to_z3.visit(expr)
    assert result == name_dict["x"] + name_dict["y"]

    expr = mp.claim.BinOpExpr(
        mp.claim.VarExpr("z"),
        mp.claim.Op.And,
        mp.claim.LiteralExpr(mp.claim.BoolValue(True)),
    )
    result = claim_to_z3.visit(expr)
    assert result == z3.And(name_dict["z"], True)

    expr = mp.claim.UnOpExpr(mp.claim.Op.Not, mp.claim.VarExpr("z"))
    result = claim_to_z3.visit(expr)
    assert result == z3.Not(name_dict["z"])

    expr = mp.claim.BinOpExpr(
        mp.claim.VarExpr("x"),
        mp.claim.Op.Eq,
        mp.claim.LiteralExpr(mp.claim.IntValue(5)),
    )
    result = claim_to_z3.visit(expr)
    assert result == (name_dict["x"] == 5)

    expr = mp.claim.UnOpExpr(mp.claim.Op.Minus, mp.claim.VarExpr("x"))
    result = claim_to_z3.visit(expr)
    assert result == -name_dict["x"]


def test_claim2z3_quantification(claim_to_z3, name_dict):
    import myprover as mp

    expr = mp.claim.QuantificationExpr(
        "FORALL",
        mp.claim.VarExpr("x"),
        mp.claim.LiteralExpr(mp.claim.IntValue(5)),
        mp.type.TypeINT,
    )
    result = claim_to_z3.visit(expr)
    assert result == z3.ForAll(name_dict["x"], True)
    assert isinstance(name_dict["x"], z3.ArithRef)

    expr = mp.claim.QuantificationExpr(
        "FORALL",
        mp.claim.VarExpr("z"),
        mp.claim.LiteralExpr(mp.claim.BoolValue(True)),
        mp.type.TypeBOOL,
    )
    claim_to_z3.visit(expr)
    assert isinstance(name_dict["z"], z3.BoolRef)
