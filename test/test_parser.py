import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def test_parser_arithmetic_operations():
    import myprover as mp

    p = mp.Parser("x == 1 + 1")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var x) Op.Eq (BinOp (Literal VInt 1) Op.Add (Literal VInt 1)))"
    )

    p = mp.Parser("xy == 1 * 11")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var xy) Op.Eq (BinOp (Literal VInt 1) Op.Mult (Literal VInt 11)))"
    )

    p = mp.Parser("x == -1 * 11")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var x) Op.Eq (BinOp (UnOp Op.Minus (Literal VInt 1)) Op.Mult (Literal VInt 11)))"
    )

    p = mp.Parser("x == -1 * -11")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (Var x) Op.Eq (BinOp (UnOp Op.Minus (Literal VInt 1)) Op.Mult (UnOp Op.Minus (Literal VInt 11))))"
    )


def test_parser_comparison_operations():
    import myprover as mp

    p = mp.Parser("x >= 7")
    e = p.parse_expr()
    assert str(e) == "(BinOp (Var x) Op.Ge (Literal VInt 7))"

    p = mp.Parser("not x")
    e = p.parse_expr()
    assert str(e) == "(UnOp Op.Not (Var x))"

    p = mp.Parser("not x >= 7")
    e = p.parse_expr()
    assert str(e) == "(UnOp Op.Not (BinOp (Var x) Op.Ge (Literal VInt 7)))"

    p = mp.Parser("not (x >= 7)")
    e = p.parse_expr()
    assert str(e) == "(UnOp Op.Not (BinOp (Var x) Op.Ge (Literal VInt 7)))"

    p = mp.Parser("(x >= 7) and (y < -1)")
    e = p.parse_expr()
    assert (
        str(e)
        == "(BinOp (BinOp (Var x) Op.Ge (Literal VInt 7)) Op.And (BinOp (Var y) Op.Lt (UnOp Op.Minus (Literal VInt 1))))"
    )


def test_parser_subscript():
    import myprover as mp

    p = mp.Parser("x[1]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Literal VInt 1))"

    p = mp.Parser("x[a]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Var a))"

    p = mp.Parser("x[1:]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Slice (Literal VInt 1) -> None))"

    p = mp.Parser("x[:10]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Slice (Literal VInt 0) -> (Literal VInt 10)))"

    p = mp.Parser("x[3:10]")
    e = p.parse_expr()
    assert str(e) == "(Subscript (Var x) (Slice (Literal VInt 3) -> (Literal VInt 10)))"

    p = mp.Parser("x[3*2:10]")
    e = p.parse_expr()
    assert (
        str(e)
        == "(Subscript (Var x) (Slice (BinOp (Literal VInt 3) Op.Mult (Literal VInt 2)) -> (Literal VInt 10)))"
    )

    p = mp.Parser("x[a+3*2:10//2]")
    e = p.parse_expr()
    assert (
        str(e)
        == "(Subscript (Var x) (Slice (BinOp (Var a) Op.Add (BinOp (Literal VInt 3) Op.Mult (Literal VInt 2))) -> (BinOp (Literal VInt 10) Op.Div (Literal VInt 2))))"
    )


def test_parse_quantification():
    import myprover as mp

    p = mp.Parser("forall x :: x == 1")
    e = p.parse_expr()
    assert (
        str(e) == "(forall  (Var x$$0):None. (BinOp (Var x$$0) Op.Eq (Literal VInt 1)))"
    )
