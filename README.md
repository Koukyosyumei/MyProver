# MyProver

```python
from myprover import invariant, precondition, postcondition, prove


@precondition("n >= 0")
@postcondition("r == n * (n + 1) / 2")
def cumsum(n):
    i = 1
    r = 0
    while i <= n:
        invariant("i <= n + 1")
        invariant("r == (i - 1) * i / 2")
        r = r + i
        i = i + 1

assert prove(cumsum, {"n": int})[0]
```