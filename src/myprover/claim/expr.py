from abc import ABCMeta, abstractmethod

from .op import Op
from .value import GeneralValue, IntValue


class Expr(metaclass=ABCMeta):
    """Abstract base class for all expression types.

    This class provides the interface for all expressions with methods for
    collecting variable names and assigning new variables.
    """

    def __init__(self) -> None:
        self._is_expr_to_verify_invriant = False

    @abstractmethod
    def collect_varnames(self):
        """Collect the variable names in the expression.

        Returns:
            set: A set of variable names.
        """
        pass

    @abstractmethod
    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        pass

    @abstractmethod
    def clone(self):
        pass


class VarExpr(Expr):
    """Represents a variable expression.

    Args:
        name (str): The name of the variable.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __repr__(self):
        return f"(Var {self.name})"

    def collect_varnames(self):
        """Collect the variable name in the variable expression.

        Returns:
            set: A set containing the variable name.
        """
        return {self.name}

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the variable expression.

        Args:
            old_var (Expr): The variable to be replaced.
            new_var (Expr): The variable to replace with.

        Returns:
            VarExpr: The updated variable expression.
        """
        if isinstance(old_var, VarExpr):
            if self.name == old_var.name:
                return new_var
            else:
                return self
        else:
            return self

    def clone(self):
        return VarExpr(self.name)


class SliceExpr(Expr):
    """Represents a slice expression.

    Args:
        lower (Expr): The lower bound of the slice.
        upper (Expr): The upper bound of the slice.
    """

    def __init__(self, lower: Expr, upper: Expr):
        super().__init__()
        self.lower = lower if lower is not None else LiteralExpr(IntValue(0))
        self.upper = upper

    def __repr__(self):
        return f"(Slice {self.lower} -> {self.upper})"

    def collect_varnames(self):
        """Collect variable names in the slice expression.

        Returns:
            set: An empty set, as slice expressions do not have variable names.
        """
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the slice expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            SliceExpr: The unchanged slice expression.
        """
        return self

    def clone(self):
        return SliceExpr(self.lower.clone(), self.upper.clone())


class SubscriptExpr(Expr):
    """Represents a subscript (indexing) expression.

    Args:
        var (Expr): The variable being subscripted.
        subscript (Expr): The subscript expression.
    """

    def __init__(self, var, subscript: Expr):
        super().__init__()
        self.var = var
        self.subscript = subscript
        self.assign={} # dict[SliceExpr, Expr]

    def __repr__(self):
        if len(self.assign) == 0:
            return f"(Subscript {self.var} {self.subscript})"
        else:
            return f"(Subscript {self.var} {self.subscript} [{self.assign}])"

    def collect_varnames(self):
        """Collect variable names in the subscript expression.

        Returns:
            set: A set of variable names in the subscript expression.
        """
        return self.var.collect_varnames().union(self.subscript.collect_varnames())

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the subscript expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            SubscriptExpr: The unchanged subscript expression.
        """
        if isinstance(old_var, SubscriptExpr) and self.var.name == old_var.var.name:
            self.assign[str(old_var.subscript)] = new_var
        else:
            for k, v in self.assign.items():
                self.assign[k] = v.assign_variable(old_var, new_var)
        return self

    def clone(self):
        return SubscriptExpr(self.var.clone(), self.subscript.clone())


class LiteralExpr(Expr):
    """Represents a literal expression.

    Args:
        v (Value): The literal value.
    """

    def __init__(self, v: GeneralValue):
        super().__init__()
        self.value = v

    def __repr__(self):
        return f"(Literal {self.value})"

    def collect_varnames(self):
        """Collect variable names in the literal expression.

        Returns:
            set: An empty set, as literal expressions do not have variable names.
        """
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the literal expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            LiteralExpr: The unchanged literal expression.
        """
        return self

    def clone(self):
        return LiteralExpr(self.value)


class UnOpExpr(Expr):
    """Represents a unary operation expression.

    Args:
        op (Op): The unary operator.
        expr (Expr): The operand expression.
    """

    def __init__(self, op: Op, expr: Expr):
        super().__init__()
        self.op = op
        self.e = expr

    def __repr__(self):
        return f"(UnOp {self.op} {self.e})"

    def collect_varnames(self):
        """Collect variable names in the unary operation expression.

        Returns:
            set: A set of variable names in the operand expression.
        """
        return {*self.e.collect_varnames()}

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the unary operation expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            UnOpExpr: The updated unary operation expression.
        """
        return UnOpExpr(self.op, self.e.assign_variable(old_var, new_var))

    def clone(self):
        return UnOpExpr(self.op, self.e.clone())


class BinOpExpr(Expr):
    """Represents a binary operation expression.

    Args:
        l (Expr): The left operand expression.
        op (Op): The binary operator.
        r (Expr): The right operand expression.
    """

    def __init__(self, l: Expr, op: Op, r: Expr):
        super().__init__()
        self.e1 = l
        self.e2 = r
        self.op = op

    def __repr__(self):
        return f"(BinOp {self.e1} {self.op} {self.e2})"

    def collect_varnames(self):
        """Collect variable names in the binary operation expression.

        Returns:
            set: A set of variable names in the left and right operand expressions.
        """
        return {*self.e1.collect_varnames(), *self.e2.collect_varnames()}

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the binary operation expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            BinOpExpr: The updated binary operation expression.
        """
        return BinOpExpr(
            self.e1.assign_variable(old_var, new_var),
            self.op,
            self.e2.assign_variable(old_var, new_var),
        )

    def clone(self):
        return BinOpExpr(self.e1.clone(), self.op, self.e2.clone())


class QuantificationExpr(Expr):
    """Represents a quantification expression.

    Args:
        quantifier (str): The quantifier ("FORALL" or "EXISTS").
        var (VarExpr): The quantified variable.
        expr (Expr): The body expression.
        var_type (str, optional): The type of the quantified variable. Defaults to None.
        bounded (bool, optional): Whether the variable is bounded. Defaults to False.
    """

    def __init__(self, quantifier, var, expr, var_type=None, bounded=False):
        super().__init__()
        self.quantifier = quantifier
        self.var = var
        self.var_type = var_type
        self.expr = expr
        self.bounded = bounded

    def sanitize(self):
        """Sanitize the quantification expression by renaming variables.

        Returns:
            QuantificationExpr or UnOpExpr: The sanitized quantification expression.
        """

        if self.bounded:
            return

        bounded_var = VarExpr(self.var.name + "$$0")
        e = self.expr.assign_variable(self.var, bounded_var)

        if self.quantifier == "EXISTS":
            # exists x. Q <==> not forall x. not Q
            return UnOpExpr(
                Op.Not,
                QuantificationExpr(
                    "FORALL", bounded_var, UnOpExpr(Op.Not, e), self.var_type, True
                ),
            )
        else:
            return QuantificationExpr("FORALL", bounded_var, e, self.var_type, True)

    def __repr__(self):
        return f"(forall  {self.var}:{self.var_type}. {self.expr})"

    def collect_varnames(self):
        """Collect variable names in the quantification expression.

        Returns:
            set: An empty set, as quantification expressions do not collect variable names directly.
        """

        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the quantification expression.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            QuantificationExpr: The updated quantification expression.
        """

        return QuantificationExpr(
            self.quantifier,
            self.var,
            self.expr.assign_variable(old_var, new_var),
            self.var_type,
            self.bounded,
        )

    def clone(self):
        return QuantificationExpr(
            self.quantifier,
            self.var.clone(),
            self.expr.clone(),
            self.var_type,
            self.bounded,
        )
