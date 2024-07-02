def precondition(precond):
    def decorator(func):
        func._precondition = precond
        return func

    return decorator


def postcondition(postcond):
    def decorator(func):
        func._postcondition = postcond
        return func

    return decorator
