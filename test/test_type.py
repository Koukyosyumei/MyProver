import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_resolve_expr_type():
    import myprover as mp

    assert mp.resolve_expr_type({}, mp.claim.LiteralExpr(mp.claim.BoolValue(True))) == (
        mp.type.TypeBOOL,
        False,
    )
    assert mp.resolve_expr_type({}, mp.claim.LiteralExpr(mp.claim.BoolValue(False))) == (
        mp.type.TypeBOOL,
        False,
    )

    assert mp.resolve_expr_type({}, mp.claim.LiteralExpr(mp.claim.IntValue(1))) == (
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
        mp.claim.UnOpExpr(mp.claim.Op.Not, mp.claim.LiteralExpr(mp.claim.BoolValue(True))),
    ) == (mp.type.TypeBOOL, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.UnOpExpr(mp.claim.Op.Minus, mp.claim.LiteralExpr(mp.claim.IntValue(1))),
    ) == (mp.type.TypeINT, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.IntValue(1)),
            mp.claim.Op.Add,
            mp.claim.LiteralExpr(mp.claim.IntValue(2)),
        ),
    ) == (mp.type.TypeINT, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.IntValue(1)),
            mp.claim.Op.Eq,
            mp.claim.LiteralExpr(mp.claim.IntValue(2)),
        ),
    ) == (mp.type.TypeBOOL, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.BinOpExpr(
            mp.claim.LiteralExpr(mp.claim.BoolValue(True)),
            mp.claim.Op.And,
            mp.claim.LiteralExpr(mp.claim.BoolValue(False)),
        ),
    ) == (mp.type.TypeBOOL, False)

    assert (
        mp.resolve_expr_type(
            {},
            mp.claim.SliceExpr(
                mp.claim.LiteralExpr(mp.claim.IntValue(0)),
                mp.claim.LiteralExpr(mp.claim.IntValue(10)),
            ),
        )
    ) == (mp.type.TypeSLICE, False)

    assert mp.resolve_expr_type(
        {},
        mp.claim.QuantificationExpr(
            "FORALL",
            mp.claim.VarExpr("x"),
            mp.claim.LiteralExpr(mp.claim.BoolValue(True)),
            mp.type.TypeINT,
        ),
    ) == (mp.type.TypeBOOL, True)

    with pytest.raises(TypeError):
        mp.resolve_expr_type(
            {},
            mp.claim.QuantificationExpr(
                "FORALL",
                mp.claim.VarExpr("x"),
                mp.claim.LiteralExpr(mp.claim.BoolValue(True)),
                None,
            ),
        )

    assert mp.resolve_expr_type(
        {"x": mp.type.TypeINT},
        mp.claim.BinOpExpr(
            mp.claim.VarExpr("x"),
            mp.claim.Op.Mult,
            mp.claim.LiteralExpr(mp.claim.IntValue(2)),
        ),
    ) == (mp.type.TypeINT, False)


def test_resolve_stmt_type():
    import myprover as mp

    env_varname2type = {}
    assert not mp.type.resolve_stmt_type(env_varname2type, mp.claim.SkipStmt())
    assert len(env_varname2type) == 0

    env_varname2type = {}
    assert not mp.type.resolve_stmt_type(
        env_varname2type, mp.claim.CompoundStmt(mp.claim.SkipStmt(), mp.claim.SkipStmt())
    )
    assert len(env_varname2type) == 0

    env_varname2type = {}
    assert mp.type.resolve_stmt_type(
        env_varname2type,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.IntValue(1))
        ),
    )
    assert len(env_varname2type) == 1
    assert env_varname2type["x"] == mp.type.TypeINT

    env_varname2type = {"x": mp.type.TypeINT}
    assert not mp.type.resolve_stmt_type(
        env_varname2type,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.IntValue(2))
        ),
    )

    env_varname2type = {"x": mp.type.TypeANY}
    assert mp.type.resolve_stmt_type(
        env_varname2type,
        mp.claim.AssignStmt(
            mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.IntValue(1))
        ),
    )
    assert len(env_varname2type) == 1
    assert env_varname2type["x"] == mp.type.TypeINT

    env_varname2type = {"x": mp.type.TypeBOOL}
    with pytest.raises(TypeError):
        mp.type.resolve_stmt_type(
            env_varname2type,
            mp.claim.AssignStmt(
                mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.IntValue(1))
            ),
        )

    env_varname2type = {}
    assert not mp.type.resolve_stmt_type(
        env_varname2type,
        mp.claim.IfElseStmt(
            mp.claim.BinOpExpr(
                mp.claim.LiteralExpr(mp.claim.IntValue(1)),
                mp.claim.Op.Eq,
                mp.claim.LiteralExpr(mp.claim.IntValue(1)),
            ),
            mp.claim.SkipStmt(),
            mp.claim.SkipStmt(),
        ),
    )
    assert len(env_varname2type) == 0

    env_varname2type = {}
    assert not mp.type.resolve_stmt_type(
        env_varname2type,
        mp.claim.AssertStmt(
            mp.claim.BinOpExpr(
                mp.claim.LiteralExpr(mp.claim.IntValue(1)),
                mp.claim.Op.Eq,
                mp.claim.LiteralExpr(mp.claim.IntValue(1)),
            )
        ),
    )
    assert len(env_varname2type) == 0

    env_varname2type = {}
    assert mp.type.resolve_stmt_type(
        env_varname2type,
        mp.claim.CompoundStmt(
            mp.claim.AssignStmt(
                mp.claim.VarExpr("x"), mp.claim.LiteralExpr(mp.claim.IntValue(1))
            ),
            mp.claim.SkipStmt(),
        ),
    )
    assert len(env_varname2type) == 1
    assert env_varname2type["x"] == mp.type.TypeINT
