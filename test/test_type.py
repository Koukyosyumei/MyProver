import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_resolve_expr_type():
    import myprover as mp

    assert mp.resolve_expr_type({}, mp.claim.LiteralExpr(mp.claim.VBool(True))) == (
        mp.type.TypeBOOL,
        False,
    )
    assert mp.resolve_expr_type({}, mp.claim.LiteralExpr(mp.claim.VBool(False))) == (
        mp.type.TypeBOOL,
        False,
    )

    assert mp.resolve_expr_type({}, mp.claim.LiteralExpr(mp.claim.VInt(1))) == (
        mp.type.TypeINT,
        False,
    )

    assert mp.resolve_expr_type({"x": mp.type.TypeINT}, mp.claim.VarExpr("x")) == (
        mp.type.TypeINT,
        False,
    )
    with pytest.raises(NotImplementedError):
        mp.resolve_expr_type({}, mp.claim.VarExpr("x"))

    assert mp.resolve_expr_type(
        {},
        mp.claim.UnOpExpr(mp.claim.Op.Not, mp.claim.LiteralExpr(mp.claim.VBool(True))),
    ) == (mp.type.TypeBOOL, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.UnOpExpr(mp.claim.Op.Minus, mp.claim.LiteralExpr(mp.claim.VInt(1))),
    ) == (mp.type.TypeINT, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.VInt(1)),
            mp.claim.Op.Add,
            mp.claim.LiteralExpr(mp.claim.VInt(2)),
        ),
    ) == (mp.type.TypeINT, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.VInt(1)),
            mp.claim.Op.Eq,
            mp.claim.LiteralExpr(mp.claim.VInt(2)),
        ),
    ) == (mp.type.TypeBOOL, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.VBool(True)),
            mp.claim.Op.And,
            mp.claim.LiteralExpr(mp.claim.VBool(False)),
        ),
    ) == (mp.type.TypeBOOL, False)

    assert (
        mp.resolve_expr_type(
            {},
            mp.claim.SliceExpr(
                mp.claim.LiteralExpr(mp.claim.VInt(0)),
                mp.claim.LiteralExpr(mp.claim.VInt(10)),
            ),
        )
    ) == (mp.type.TypeSLICE, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.QuantificationExpr(
            "FORALL",
            mp.claim.VarExpr("x"),
            mp.claim.LiteralExpr(mp.claim.VBool(True)),
            mp.type.TypeINT,
        ),
    ) == (mp.type.TypeBOOL, True)

    with pytest.raises(TypeError):
        mp.resolve_expr_type(
            {},
            mp.claim.QuantificationExpr(
                "FORALL",
                mp.claim.VarExpr("x"),
                mp.claim.LiteralExpr(mp.claim.VBool(True)),
                None,
            ),
        )

    assert mp.resolve_expr_type(
        {"x": mp.type.TypeINT},
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"),
            mp.claim.Op.Mult,
            mp.claim.LiteralExpr(mp.claim.VInt(2)),
        ),
    ) == (mp.type.TypeINT, False)


def test_resolve_stmt_type():
    import myprover as mp

    sigma = {}
    assert not mp.type.resolve_stmt_type(sigma, mp.claim.SkipStmt())
    assert len(sigma) == 0

    sigma = {}
    assert not mp.type.resolve_stmt_type(
        sigma, mp.claim.SeqStmt(mp.claim.SkipStmt(), mp.claim.SkipStmt())
    )
    assert len(sigma) == 0

    sigma = {}
    assert mp.type.resolve_stmt_type(
        sigma,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
        ),
    )
    assert len(sigma) == 1
    assert sigma["x"] == mp.type.TypeINT

    sigma = {"x": mp.type.TypeINT}
    assert not mp.type.resolve_stmt_type(
        sigma,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(2))
        ),
    )

    sigma = {"x": mp.type.TypeANY}
    assert mp.type.resolve_stmt_type(
        sigma,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
        ),
    )
    assert len(sigma) == 1
    assert sigma["x"] == mp.type.TypeINT

    sigma = {"x": mp.type.TypeBOOL}
    with pytest.raises(TypeError):
        mp.type.resolve_stmt_type(
            sigma,
            mp.claim.AssignStmt(
                mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
            ),
        )

    sigma = {}
    assert not mp.type.resolve_stmt_type(
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

    sigma = {}
    assert not mp.type.resolve_stmt_type(
        sigma,
        mp.claim.AssertStmt(
            mp.claim.BinOpExpr(
                mp.claim.LiteralExpr(mp.claim.VInt(1)),
                mp.claim.Op.Eq,
                mp.claim.LiteralExpr(mp.claim.VInt(1)),
            )
        ),
    )
    assert len(sigma) == 0

    sigma = {}
    assert mp.type.resolve_stmt_type(
        sigma,
        mp.claim.SeqStmt(
            mp.claim.AssignStmt(
                mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.VInt(1))
            ),
            mp.claim.SkipStmt(),
        ),
    )
    assert len(sigma) == 1
    assert sigma["x"] == mp.type.TypeINT
