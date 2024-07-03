import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_parser_arithmetic_operations():
    import myprover as mp

    p = mp.ClaimParser("x == 1 + 1")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var x) Op.Eq (BinOp (Literal IntValue 1) Op.Add (Literal IntValue 1)))"
    )

    p = mp.ClaimParser("xy == 1 * 11")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var xy) Op.Eq (BinOp (Literal IntValue 1) Op.Mult (Literal IntValue 11)))"
    )

    p = mp.ClaimParser("x == -1 * 11")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var x) Op.Eq (BinOp (UnOp Op.Minus (Literal IntValue 1)) Op.Mult (Literal IntValue 11)))"
    )

    p = mp.ClaimParser("x == -1 * -11")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var x) Op.Eq (BinOp (UnOp Op.Minus (Literal IntValue 1)) Op.Mult (UnOp Op.Minus (Literal IntValue 11))))"
    )


def test_parser_comparison_operations():
    import myprover as mp

    p = mp.ClaimParser("x >= 7")
    e = p.parse_expr()
    assert str(e) == "(BinOp (Var x) Op.Ge (Literal IntValue 7))"

    p = mp.ClaimParser("not x")
    e = p.parse_expr()
    assert str(e) == "(UnOp Op.Not (Var x))"

    p = mp.ClaimParser("not x >= 7")
    e = p.parse_expr()
    assert str(e) == "(UnOp Op.Not (BinOp (Var x) Op.Ge (Literal IntValue 7)))"

    p = mp.ClaimParser("not (x >= 7)")
    e = p.parse_expr()
    assert str(e) == "(UnOp Op.Not (BinOp (Var x) Op.Ge (Literal IntValue 7)))"

    p = mp.ClaimParser("(x >= 7) and (y < -1)")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (BinOp (Var x) Op.Ge (Literal IntValue 7)) Op.And (BinOp (Var y) Op.Lt (UnOp Op.Minus (Literal IntValue 1))))"
    )


def test_parser_subscript():
    import myprover as mp

    p = mp.ClaimParser("x[1]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Literal IntValue 1))"

    p = mp.ClaimParser("x[a]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Var a))"

    p = mp.ClaimParser("x[1:]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Slice (Literal IntValue 1) -> None))"

    p = mp.ClaimParser("x[:10]")
    e = p.parse_expr()
    assert (
        str(e)
        == "(Subscript (Var x) (Slice (Literal IntValue 0) -> (Literal IntValue 10)))"
    )

    p = mp.ClaimParser("x[3:10]")
    e = p.parse_expr()
    assert (
        str(e)
        == "(Subscript (Var x) (Slice (Literal IntValue 3) -> (Literal IntValue 10)))"
    )

    p = mp.ClaimParser("x[3*2:10]")
    e = p.parse_expr()
    assert (
        str(e)
        == "(Subscript (Var x) (Slice (BinOp (Literal IntValue 3) Op.Mult (Literal IntValue 2)) -> (Literal IntValue 10)))"
    )

    p = mp.ClaimParser("x[a+3*2:10/2]")
    e = p.parse_expr()
    assert (
        str(e)
        == "(Subscript (Var x) (Slice (BinOp (Var a) Op.Add (BinOp (Literal IntValue 3) Op.Mult (Literal IntValue 2))) -> (BinOp (Literal IntValue 10) Op.Div (Literal IntValue 2))))"
    )


def test_parse_quantification():
    import myprover as mp

    p = mp.ClaimParser("forall x :: x == 1")
    e = p.parse_expr()
    assert (
        str(e)
        == "(forall  (Var x$$0):None. (BinOp (Var x$$0) Op.Eq (Literal IntValue 1)))"
    )
