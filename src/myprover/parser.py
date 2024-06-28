import re
from .claim import (
    QuantificationExpr,
    BinOpExpr,
    Op,
    UnOpExpr,
    LiteralExpr,
    VInt,
    VBool,
    VarExpr,
    SliceExpr,
    SubscriptExpr,
)

"""
expr           = quantification || logocal
quantification = ('forall' | 'exists') (var | var [:var]) '::' logical
logical        = "not" equality | equality ("and" equality | "or" equality | "==>" equality | "<==>" equality)*
equality       = relational ("==" relational | "!=" relational)*
relational     = add ("<" add | "<=" add | ">" add | ">=" add)*
add            = mul ("+" mul | "-" mul)*
mul            = unary ("*" unary | "/" unary)*
unary          = ("+" | "-")? primary
primary        = bool
               | num
               | var
               | subscript
               | '(' expr ')'

bool           = 'True' | 'False'
num            = [0-9]+
var            = [a-zA-Z_][a-zA-Z0-9_]*
subscript      = var '[' add ']' | var '[' add `:` ']' | var '[' `:` add ']' | var '[' add `:` add ']'
"""


# Tokenizer
token_specification = [
    ("INT", r"\d+"),
    ("BOOL", r"\b(True|False)\b"),
    ("VAR", r"[A-Za-z_]\w*"),
    # ("NEG", r"-"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MULT", r"\*"),
    ("DIV", r"//"),
    ("MOD", r"%"),
    ("AND", r"\band\b"),
    ("OR", r"\bor\b"),
    ("NOT", r"\bnot\b"),
    ("IMPLIES", r"==>"),
    ("IFF", r"<==>"),
    ("FORALL", r"\bforall\b"),
    ("EXISTS", r"\bexists\b"),
    ("LT", r"<"),
    ("LE", r"<="),
    ("GT", r">"),
    ("GE", r">="),
    ("EQ", r"=="),
    ("NEQ", r"!="),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("COMMA", r","),
    ("COLON", r":"),
    ("DOUBLECOLON", r"::"),
    ("WHITESPACE", r"\s+"),
]

token_regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in token_specification)
tokens = re.compile(token_regex)


# Parser
# Tokenizer
token_specification = [
    ("INT", r"\d+"),
    ("BOOL", r"\b(True|False)\b"),
    # ("NEG", r"-"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MULT", r"\*"),
    ("DIV", r"//"),
    ("MOD", r"%"),
    ("AND", r"\band\b"),
    ("OR", r"\bor\b"),
    ("NOT", r"\bnot\b"),
    ("IFF", r"<==>"),
    ("IMPLIES", r"==>"),
    ("FORALL", r"\bforall\b"),
    ("EXISTS", r"\bexists\b"),
    ("LE", r"<="),
    ("LT", r"<"),
    ("GE", r">="),
    ("GT", r">"),
    ("EQ", r"=="),
    ("NEQ", r"!="),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("COMMA", r","),
    ("DOUBLECOLON", r"::"),
    ("COLON", r":"),
    ("VAR", r"[A-Za-z_]\w*"),
    ("WHITESPACE", r"\s+"),
]

token_regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in token_specification)
tokens = re.compile(token_regex)


# Parser
class Parser:
    def __init__(self, text):
        self.tokens = [
            match for match in tokens.finditer(text) if match.lastgroup != "WHITESPACE"
        ]
        self.pos = -1

    def consume(self, expected_token):
        if self.pos + 1 >= len(self.tokens):
            return False
        if self.tokens[self.pos + 1].lastgroup == expected_token:
            self.pos += 1
            return True
        return False

    def next_token(self):
        if self.pos < len(self.tokens):
            self.pos += 1
        # raise RuntimeError("Already reached the end of tokens")

    def current_token(self):
        if self.pos == -1:
            raise RuntimeError("self.pos == -1")
        elif self.pos < len(self.tokens):
            return self.tokens[self.pos]
        else:
            return None

    def parse_expr(self):
        if self.consume("FORALL") or self.consume("EXISTS"):
            # quantification = ('forall' | 'exists') (var | var [:var]) '::' logical
            quantifier = self.current_token().lastgroup
            var = self.parse_primary()
            print(type(var))
            # raise RuntimeError(f"Expect `VAR` at pos={self.pos}")
            var_type = None
            if self.consume("COLON"):
                self.next_token()
                var_type = self.parse_primary()
            if self.consume("DOUBLECOLON"):
                assertion_expr = self.parse_expr()
                return QuantificationExpr(
                    quantifier, var, assertion_expr, var_type
                ).sanitize()
            else:
                raise ValueError(f"Expect `::` at pos={self.pos}")
        else:
            return self.parse_logical()

    def parse_logical(self):
        """
        logical = "not" equality | equality ("and" equality | "or" equality | "==>" equality | "<==>" equality)*
        """
        if self.consume("NOT"):
            return UnOpExpr(Op.Not, self.parse_equality())
        else:
            left_expr = self.parse_equality()

            while True:
                if self.consume("AND"):
                    left_expr = BinOpExpr(left_expr, Op.And, self.parse_equality())
                elif self.consume("OR"):
                    left_expr = BinOpExpr(left_expr, Op.Or, self.parse_equality())
                elif self.consume("IMPLIES"):
                    left_expr = BinOpExpr(left_expr, Op.Implies, self.parse_equality())
                elif self.consume("IFF"):
                    left_expr = BinOpExpr(left_expr, Op.Iff, self.parse_equality())
                else:
                    return left_expr

    def parse_equality(self):
        """
        equality = relational ("==" relational | "!=" relational)*
        """
        left_expr = self.parse_relational()

        while True:
            if self.consume("EQ"):
                left_expr = BinOpExpr(left_expr, Op.Eq, self.parse_relational())
            elif self.consume("NEQ"):
                left_expr = BinOpExpr(left_expr, Op.NEq, self.parse_relational())
            else:
                return left_expr

    def parse_relational(self):
        """
        relational = add ("<" add | "<=" add | ">" add | ">=" add)*
        """
        left_expr = self.parse_add()

        while True:
            if self.consume("LT"):
                left_expr = BinOpExpr(left_expr, Op.Lt, self.parse_add())
            elif self.consume("LE"):
                left_expr = BinOpExpr(left_expr, Op.Le, self.parse_add())
            elif self.consume("GT"):
                left_expr = BinOpExpr(left_expr, Op.Gt, self.parse_add())
            elif self.consume("GE"):
                left_expr = BinOpExpr(left_expr, Op.Ge, self.parse_add())
            else:
                return left_expr

    def parse_add(self):
        """
        add = mul ("+" mul | "-" mul)*
        """
        left_expr = self.parse_mul()

        while True:
            if self.consume("PLUS"):
                left_expr = BinOpExpr(left_expr, Op.Add, self.parse_mul())
            elif self.consume("MINUS"):
                left_expr = BinOpExpr(left_expr, Op.Minus, self.parse_mul())
            else:
                return left_expr

    def parse_mul(self):
        """
        mul = unary ("*" unary | "/" unary)*
        """
        left_expr = self.parse_unary()

        while True:
            if self.consume("MULT"):
                left_expr = BinOpExpr(left_expr, Op.Mult, self.parse_unary())
            elif self.consume("DIV"):
                left_expr = BinOpExpr(left_expr, Op.Div, self.parse_unary())
            elif self.consume("MOD"):
                left_expr = BinOpExpr(left_expr, Op.Mod, self.parse_unary())
            else:
                return left_expr

    def parse_unary(self):
        """
        unary = ("+" | "-")? primary
        """
        if self.consume("PLUS"):
            return UnOpExpr(Op.Add, self.parse_primary())
        elif self.consume("MINUS"):
            return UnOpExpr(Op.Minus, self.parse_primary())
        else:
            return self.parse_primary()

    def parse_primary(self):
        if self.consume("LPAREN"):
            expr = self.parse_expr()
            self.next_token()
            token = self.current_token()
            if token.lastgroup != "RPAREN":
                raise ValueError(f"Expect ')' at pos={self.pos}")
            return expr
        else:
            if self.consume("INT"):
                token = self.current_token()
                value = token.group(0)
                return LiteralExpr(VInt(int(value)))
            elif self.consume("BOOL"):
                return LiteralExpr(VBool(value == "True"))
            elif self.consume("VAR"):
                token = self.current_token()
                value = token.group(0)
                var_expr = VarExpr(value)

                if self.consume("LBRACKET"):
                    token = self.current_token()
                    if token is None:
                        raise ValueError(f"Uncompleted `[` at pos={self.pos}")
                    elif self.consume("COLON"):
                        # var '[' `:` add ']'
                        right_expr = self.parse_add()
                        return SubscriptExpr(var_expr, SliceExpr(None, right_expr))
                    else:
                        left_expr = self.parse_add()
                        if self.consume("COLON"):
                            if self.consume("RBRACKET"):
                                # var '[' add `:` ']'
                                return SubscriptExpr(
                                    var_expr, SliceExpr(left_expr, None)
                                )
                            else:
                                # var '[' add `:` add ']'
                                right_expr = self.parse_add()
                                return SubscriptExpr(
                                    var_expr, SliceExpr(left_expr, right_expr)
                                )
                        else:
                            # var '[' add ']'
                            if not self.consume("RBRACKET"):
                                raise ValueError(f"Expect `]` at pos={self.pos}")
                            return SubscriptExpr(var_expr, left_expr)
                else:
                    return var_expr
