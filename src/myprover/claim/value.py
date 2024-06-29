class Value:
    __slots__ = ["v"]

    def __init__(self, v):
        self.v = v


class VInt(Value):
    def __init__(self, v):
        super().__init__(int(v))

    def __str__(self):
        return f"VInt {self.v}"

    def __repr__(self):
        return f"VInt {self.v}"


class VBool(Value):
    def __init__(self, v):
        super().__init__(v == "True" or v == True)

    def __str__(self):
        return f"VBool {self.v}"

    def __repr__(self):
        return f"VBool {self.v}"
