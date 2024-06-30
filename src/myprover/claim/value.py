class GeneralValue:
    """A general value class that serves as a base for specific value types.

    Attributes:
        v: The value stored in the instance.
    """

    __slots__ = ["v"]

    def __init__(self, v):
        self.v = v


class IntValue(GeneralValue):
    """Represents an integer value.

    Inherits from GeneralValue and ensures the value is an integer.

    Args:
        v: The integer value to be stored.
    """

    def __init__(self, v):
        super().__init__(int(v))

    def __str__(self):
        return f"IntValue {self.v}"

    def __repr__(self):
        return f"IntValue {self.v}"


class BoolValue(GeneralValue):
    """Represents a boolean value.

    Inherits from GeneralValue and ensures the value is a boolean.

    Args:
        v: The boolean value to be stored.
    """
    
    def __init__(self, v):
        super().__init__(v == "True" or v == True)

    def __str__(self):
        return f"BoolValue {self.v}"

    def __repr__(self):
        return f"BoolValue {self.v}"
