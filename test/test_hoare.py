import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_weakest_precondition():
    import myprover as mp

    result = mp.weakest_precondition(
        mp.claim.SkipStmt(), mp.claim.LiteralExpr(mp.claim.VBool(True)), {}
    )
    assert str(result[0]) == "(Literal VBool True)"
    assert len(result[1]) == 0
