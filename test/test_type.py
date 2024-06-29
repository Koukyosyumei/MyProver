import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_type_infer_expr():
    import myprover as mp

    assert mp.type_infer_expr({}, mp.claim.LiteralExpr(mp.claim.VBool(True))) == (
        mp.type.TypeBOOL,
        False,
    )
    assert mp.type_infer_expr({}, mp.claim.LiteralExpr(mp.claim.VBool(False))) == (
        mp.type.TypeBOOL,
        False,
    )

    assert mp.type_infer_expr({}, mp.claim.LiteralExpr(mp.claim.VInt(1))) == (
        mp.type.TypeINT,
        False,
    )

    assert mp.type_infer_expr({"x": mp.type.TypeINT}, mp.claim.VarExpr("x")) == (
        mp.type.TypeINT,
        False,
    )
    with pytest.raises(NotImplementedError):
        mp.type_infer_expr({}, mp.claim.VarExpr("x"))

    assert mp.type_infer_expr(
        {},
        mp.claim.UnOpExpr(mp.claim.Op.Not, mp.claim.LiteralExpr(mp.claim.VBool(True))),
    ) == (mp.type.TypeBOOL, False)

    assert mp.type_infer_expr(
        {},
        mp.claim.UnOpExpr(mp.claim.Op.Minus, mp.claim.LiteralExpr(mp.claim.VInt(1))),
    ) == (mp.type.TypeINT, False)

    assert mp.type_infer_expr(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.VInt(1)),
            mp.claim.Op.Add,
            mp.claim.LiteralExpr(mp.claim.VInt(2)),
        ),
    ) == (mp.type.TypeINT, False)

    assert mp.type_infer_expr(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.VInt(1)),
            mp.claim.Op.Eq,
            mp.claim.LiteralExpr(mp.claim.VInt(2)),
        ),
    ) == (mp.type.TypeBOOL, False)

    assert mp.type_infer_expr(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.VBool(True)),
            mp.claim.Op.And,
            mp.claim.LiteralExpr(mp.claim.VBool(False)),
        ),
    ) == (mp.type.TypeBOOL, False)

    assert (
        mp.type_infer_expr(
            {},
            mp.claim.SliceExpr(
                mp.claim.LiteralExpr(mp.claim.VInt(0)),
                mp.claim.LiteralExpr(mp.claim.VInt(10)),
            ),
        )
    ) == (mp.type.TypeSLICE, False)

    assert mp.type_infer_expr(
        {},
        mp.claim.QuantificationExpr(
            "FORALL",
            mp.claim.VarExpr("x"),
            mp.claim.LiteralExpr(mp.claim.VBool(True)),
            mp.type.TypeINT,
        ),
    ) == (mp.type.TypeBOOL, True)

    with pytest.raises(TypeError):
        mp.type_infer_expr(
            {},
            mp.claim.QuantificationExpr(
                "FORALL",
                mp.claim.VarExpr("x"),
                mp.claim.LiteralExpr(mp.claim.VBool(True)),
                None,
            ),
        )

    assert mp.type_infer_expr(
        {"x": mp.type.TypeINT},
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"),
            mp.claim.Op.Mult,
            mp.claim.LiteralExpr(mp.claim.VInt(2)),
        ),
    ) == (mp.type.TypeINT, False)


def test_type_infer_stmt():
    import myprover as mp

    sigma = {}
    assert not mp.type.type_infer_stmt(sigma, mp.claim.SkipStmt())
    assert len(sigma) == 0

    sigma = {}
    assert not mp.type.type_infer_stmt(
        sigma, mp.claim.SeqStmt(mp.claim.SkipStmt(), mp.claim.SkipStmt())
    )
    assert len(sigma) == 0

    sigma = {}
    assert mp.type.type_infer_stmt(
        sigma,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
        ),
    )
    assert len(sigma) == 1
    assert sigma["x"] == mp.type.TypeINT

    sigma = {"x": mp.type.TypeINT}
    assert not mp.type.type_infer_stmt(
        sigma,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(2))
        ),
    )

    sigma = {"x": mp.type.TypeANY}
    assert mp.type.type_infer_stmt(
        sigma,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
        ),
    )
    assert len(sigma) == 1
    assert sigma["x"] == mp.type.TypeINT

    sigma = {"x": mp.type.TypeBOOL}
    with pytest.raises(TypeError):
        mp.type.type_infer_stmt(
            sigma,
            mp.claim.AssignStmt(
                mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
            ),
        )

    sigma = {}
    assert not mp.type.type_infer_stmt(
        sigma,
        mp.claim.IfStmt(
            mp.claim.BinOpExpr(
                mp.claim.LiteralExpr(mp.claim.VInt(1)),
                mp.claim.Op.Eq,
                mp.claim.LiteralExpr(mp.claim.VInt(1)),
            ),
            mp.claim.SkipStmt(),
            mp.claim.SkipStmt(),
        ),
    )
    assert len(sigma) == 0
