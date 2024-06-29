from enum import Enum


class OpType:
    def __init__(self, name, isArith, isComp, isBool):
        self.name = name
        self.isArith = isArith
        self.isComp = isComp
        self.isBool = isBool

    def __repr__(self):
        return self.name


class Op(Enum):
    # Arithmetic Operations
    Add = OpType("+", True, False, False)
    Minus = OpType("-", True, False, False)
    Mult = OpType("*", True, False, False)
    Div = OpType("/", True, False, False)
    Mod = OpType("%", True, False, False)

    # Comparison Operators
    Eq = OpType("==", False, True, False)
    NEq = OpType("!=", False, True, False)
    Lt = OpType("<", False, True, False)
    Le = OpType("<=", False, True, False)
    Gt = OpType(">", False, True, False)
    Ge = OpType("=>", False, True, False)

    # Boolen Operators
    And = OpType("and", False, False, True)
    Or = OpType("or", False, False, True)
    Not = OpType("not", False, False, True)
    Implies = OpType("==>", False, False, True)
    Iff = OpType("<==>", False, False, True)
