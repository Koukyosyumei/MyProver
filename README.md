# MyProver

```python
from myprover import MyProver, invariant, assume


def func(n):
    i = 1
    r = 0
    while i <= n:
        invariant("i <= n + 1")
        invariant("r == (i - 1) * i // 2")
        r = r + i
        i = i + 1

code = inspect.getsource(func)
code = code.lstrip()

precond = "n >= 0"
postcond = "r == n * (n + 1) // 2"

prover = MyProver()
prover.register("func", {"n": int})
assert prover.verify(func, "func", precond, postcond)
```