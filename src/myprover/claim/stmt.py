from abc import ABCMeta, abstractmethod

from .expr import Expr


class Stmt(metaclass=ABCMeta):
    """Abstract base class for all statement types.

    This class provides the interface for all statements with a method for
    collecting variable names.
    """

    @abstractmethod
    def collect_assigned_varnames(self):
        """Collect the variable names in the statement.

        Returns:
            set: A set of variable names.
        """
        pass

    @abstractmethod
    def collect_havoced_varnames(self):
        """Collect the variable names in the statement.

        Returns:
            set: A set of variable names.
        """
        pass

    @abstractmethod
    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

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


class SkipStmt(Stmt):
    """Represents a skip statement that does nothing."""

    def __repr__(self):
        return f"(Skip)"

    def collect_assigned_varnames(self):
        """Collect variable names in the skip statement.

        Returns:
            set: An empty set, as skip statements do not have variable names.
        """
        return set()

    def collect_havoced_varnames(self):
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        pass

    def clone(self):
        return SkipStmt()


class AssignStmt(Stmt):
    """Represents an assignment statement.

    Args:
        var (VarExpr): The variable being assigned to.
        expr (Expr): The expression being assigned.
    """

    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def __repr__(self):
        return f"(Assign {self.var} {self.expr})"

    def collect_assigned_varnames(self):
        """Collect variable names in the assignment statement.

        Returns:
            set: A set of variable names in the assignment statement.
        """
        return {self.var.name}

    def collect_havoced_varnames(self):
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        return AssignStmt(
            self.var.assign_variable(old_var, new_var),
            self.expr.assign_variable(old_var, new_var),
        )

    def clone(self):
        return AssignStmt(self.var.clone(), self.expr.clone())


class IfElseStmt(Stmt):
    """Represents an if statement.

    Args:
        cond_expr (Expr): The condition expression.
        then_stmt (Stmt): The statement to execute if the condition is true.
        else_stmt (Stmt): The statement to execute if the condition is false.
    """

    def __init__(self, cond_expr: Expr, then_stmt: Stmt, else_stmt: Stmt):
        self.cond = cond_expr
        self.then_branch = then_stmt if then_stmt is not None else SkipStmt()
        self.else_branch = else_stmt if else_stmt is not None else SkipStmt()

    def __repr__(self):
        return f"(If {self.cond} {self.then_branch} {self.else_branch})"

    def collect_assigned_varnames(self):
        """Collect variable names in the if statement.

        Returns:
            set: A set of variable names in the if statement.
        """
        return {
            *self.then_branch.collect_assigned_varnames(),
            *self.else_branch.collect_assigned_varnames(),
        }

    def collect_havoced_varnames(self):
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        return IfElseStmt(
            self.cond.assign_variable(old_var, new_var),
            self.then_branch.assign_variable(old_var, new_var),
            self.else_branch.assign_variable(old_var, new_var),
        )

    def clone(self):
        return IfElseStmt(
            self.cond.clone(), self.then_branch.clone(), self.else_branch.clone()
        )


class CompoundStmt(Stmt):
    """Represents a sequence of statements.

    Args:
        s1 (Stmt): The first statement in the sequence.
        s2 (Stmt): The second statement in the sequence.
    """

    def __init__(self, s1: Stmt, s2: Stmt):
        self.s1 = s1 if s1 is not None else SkipStmt()
        self.s2 = s2 if s2 is not None else SkipStmt()

    def __repr__(self):
        return f"(Seq {self.s1} {self.s2})"

    def collect_assigned_varnames(self):
        """Collect variable names in the sequence of statements.

        Returns:
            set: A set of variable names in the sequence of statements.
        """
        return {
            *self.s1.collect_assigned_varnames(),
            *self.s2.collect_assigned_varnames(),
        }

    def collect_havoced_varnames(self):
        return {
            *self.s1.collect_havoced_varnames(),
            *self.s2.collect_havoced_varnames(),
        }

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        return CompoundStmt(
            self.s1.assign_variable(old_var, new_var),
            self.s2.assign_variable(old_var, new_var),
        )

    def clone(self):
        return CompoundStmt(self.s1.clone(), self.s2.clone())


class AssumeStmt(Stmt):
    """Represents an assume statement.

    Args:
        e (Expr): The expression to assume.
    """

    def __init__(self, e: Expr):
        self.e = e

    def __repr__(self):
        return f"(Assume {self.e})"

    def collect_assigned_varnames(self):
        """Collect variable names in the assume statement.

        Returns:
            set: A set of variable names in the assume statement.
        """
        return set()  # {*self.e.collect_assigned_varnames()}

    def collect_havoced_varnames(self):
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        return AssumeStmt(self.e.assign_variable(old_var, new_var))

    def clone(self):
        return AssumeStmt(self.e.clone())


class AssertStmt(Stmt):
    """Represents an assert statement.

    Args:
        e (Expr): The expression to assert.
    """

    def __init__(self, e):
        self.e = e

    def __repr__(self):
        return f"(Assert {self.e})"

    def collect_assigned_varnames(self):
        """Collect variable names in the assert statement.

        Returns:
            set: A set of variable names in the assert statement.
        """
        return set()  # {*self.e.collect_assigned_varnames()}

    def collect_havoced_varnames(self):
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        return AssertStmt(self.e.assign_variable(old_var, new_var))

    def clone(self):
        return AssertStmt(self.e.clone())


class WhileStmt(Stmt):
    """Represents a while statement.

    Args:
        invariant (Expr): The invariant expression.
        cond (Expr): The condition expression.
        body (Stmt): The body statement to execute while the condition is true.
    """

    def __init__(self, invariant: Expr, cond: Expr, body: Stmt):
        self.invariant = invariant
        self.cond = cond
        self.body = body if body is not None else SkipStmt()

    def __repr__(self):
        return f"(While {self.cond} {self.body})"

    def collect_assigned_varnames(self):
        """Collect variable names in the while statement.

        Returns:
            set: A set of variable names in the while statement.
        """
        return {*self.body.collect_assigned_varnames()}

    def collect_havoced_varnames(self):
        return set()

    def assign_variable(self, old_var, new_var):
        """Assign a new variable in place of an old variable in the statament.

        Args:
            old_var (VarExpr): The variable to be replaced.
            new_var (VarExpr): The variable to replace with.

        Returns:
            Expr: The updated expression.
        """
        return WhileStmt(
            self.invariant.assign_variable(old_var, new_var),
            self.cond.assign_variable(old_var, new_var),
            self.body.assign_variable(old_var, new_var),
        )

    def clone(self):
        return WhileStmt(self.invariant.clone(), self.cond.clone(), self.body.clone())


class HavocStmt(Stmt):
    """Represents a havoc statement that can assign any value to a variable.

    Args:
        var_name (str): The name of the variable to havoc.
        num_havoced (int): How many times this variable is havoced.
    """

    def __init__(self, var_name: str, num_havoced: int = 0):
        self.var_name = var_name
        self.num_havoced = num_havoced

    def __repr__(self):
        return f"(Havoc {self.var_name})"

    def collect_assigned_varnames(self):
        """Collect variable names in the havoc statement.

        Returns:
            set: An empty set, as havoc statements do not have variable names.
        """
        return set()

    def collect_havoced_varnames(self):
        return {self.var_name}

    def assign_variable(self, old_var, new_var):
        pass

    def clone(self):
        return HavocStmt(self.var_name)
