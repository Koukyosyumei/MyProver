class InvalidInvariantError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)

class VerificationFailureError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)