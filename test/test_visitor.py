import ast
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_py2claim():
    import myprover as mp

    source = "a = 1 + 1\nb = 5 * 2"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (Assign a (BinOp (Literal VInt 1) Op.Add (Literal VInt 1))) (Assign b (BinOp (Literal VInt 5) Op.Mult (Literal VInt 2))))"
    )

    source = "x <= 2\nx == 2"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (BinOp (Var x) Op.Le (Literal VInt 2)) (BinOp (Var x) Op.Eq (Literal VInt 2)))"
    )

    source = "if x == 1:\n    y = 30 % 2\nelse:\n    z = 2"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (If (BinOp (Var x) Op.Eq (Literal VInt 1)) (Seq (Assign y (BinOp (Literal VInt 30) Op.Mod (Literal VInt 2))) (Skip)) (Seq (Assign z (Literal VInt 2)) (Skip))) (Skip))"
    )

    source = "x = y[1:]\nx = y[:1]\nx = y[1:3]"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (Seq (Assign x (Subscript (Var y) (Slice (Literal VInt 1) -> None))) (Assign x (Subscript (Var y) (Slice (Literal VInt 0) -> (Literal VInt 1))))) (Assign x (Subscript (Var y) (Slice (Literal VInt 1) -> (Literal VInt 3)))))"
    )

    source = "def f(n):\n    while x > 0:\n        x = x - 1"
    py_tree = ast.parse(source)
    mp_tree = mp.PyToClaim().visit(py_tree)
    assert (
        str(mp_tree)
        == "(Seq (Seq (Seq (Assert (Literal VBool True)) (Havoc x)) (Assume (Literal VBool True))) (If (BinOp (Var x) Op.Gt (Literal VInt 0)) (Seq (Seq (Seq (Assign x (BinOp (Var x) Op.Minus (Literal VInt 1))) (Skip)) (Assert (Literal VBool True))) (Assume (Literal VBool False))) (Skip)))"
    )
