import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_derive_weakest_precondition_simple():
    import myprover as mp

    result = mp.derive_weakest_precondition(
        mp.claim.SkipStmt(), mp.claim.LiteralExpr(mp.claim.VBool(True)), {}
    )
    assert str(result[0]) == "(Literal VBool True)"
    assert len(result[1]) == 0

    result = mp.derive_weakest_precondition(
        mp.claim.AssignStmt(mp.claim.VarExpr("x"), mp.claim.VarExpr("y")),
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"), mp.claim.Op.Eq, mp.claim.LiteralExpr(1)
        ),
        {"x": int, "y": int},
    )
    assert str(result[0]) == "(BinOp (Var y) Op.Eq (Literal 1))"
    assert len(result[1]) == 0

    result = mp.derive_weakest_precondition(
        mp.claim.SeqStmt(
            mp.claim.SkipStmt(),
            mp.claim.AssignStmt(mp.claim.VarExpr("x"), mp.claim.LiteralExpr(1)),
        ),
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"), mp.claim.Op.Eq, mp.claim.LiteralExpr(1)
        ),
        {"x": int},
    )
    assert str(result[0]) == "(BinOp (Literal 1) Op.Eq (Literal 1))"
    assert len(result[1]) == 0

    result = mp.derive_weakest_precondition(
        mp.claim.IfStmt(
            mp.claim.BinOpExpr(
                mp.claim.VarExpr("x"), mp.claim.Op.Eq, mp.claim.LiteralExpr(1)
            ),
            mp.claim.SkipStmt(),
            mp.claim.AssignStmt(mp.claim.VarExpr("x"), mp.claim.VarExpr("y")),
        ),
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"), mp.claim.Op.Eq, mp.claim.LiteralExpr(1)
        ),
        {"x": int},
    )
    assert (
        str(result[0])
        == "(BinOp (BinOp (BinOp (Var x) Op.Eq (Literal 1)) Op.Implies (BinOp (Var x) Op.Eq (Literal 1))) Op.And (BinOp (UnOp Op.Not (BinOp (Var x) Op.Eq (Literal 1))) Op.Implies (BinOp (Var y) Op.Eq (Literal 1))))"
    )
    assert len(result[1]) == 0

    result = mp.derive_weakest_precondition(
        mp.claim.WhileStmt(
            mp.claim.BinOpExpr(
                mp.claim.VarExpr("x"), mp.claim.Op.Ge, mp.claim.LiteralExpr(0)
            ),
            mp.claim.BinOpExpr(
                mp.claim.VarExpr("x"), mp.claim.Op.Le, mp.claim.LiteralExpr(10)
            ),
            mp.claim.AssignStmt(
                mp.claim.VarExpr("x"),
                mp.claim.BinOpExpr(
                    mp.claim.VarExpr("x"), mp.claim.Op.Add, mp.claim.LiteralExpr(1)
                ),
            ),
        ),
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"), mp.claim.Op.Eq, mp.claim.LiteralExpr(55)
        ),
        {"x": int},
    )
    assert str(result[0]) == "(BinOp (Var x) Op.Ge (Literal 0))"
    assert len(result[1]) == 2
    ac_strs = {str(e) for e in result[1]}
    assert (
        "(BinOp (BinOp (BinOp (Var x) Op.Ge (Literal 0)) Op.And (BinOp (Var x) Op.Le (Literal 10))) Op.Implies (BinOp (BinOp (Var x) Op.Add (Literal 1)) Op.Ge (Literal 0)))"
        in ac_strs
    )
    assert (
        "(BinOp (BinOp (BinOp (Var x) Op.Ge (Literal 0)) Op.And (UnOp Op.Not (BinOp (Var x) Op.Le (Literal 10)))) Op.Implies (BinOp (Var x) Op.Eq (Literal 55)))"
        in ac_strs
    )
