class DomainError(Exception):
    status_code = 400
    code = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class ValidationError(DomainError):
    status_code = 422
    code = "validation_error"


class AuthenticationError(DomainError):
    status_code = 401
    code = "authentication_required"


class AuthorizationError(DomainError):
    status_code = 403
    code = "forbidden"


class InvalidTransitionError(DomainError):
    status_code = 409
    code = "invalid_transition"


class ConfigurationError(DomainError):
    status_code = 503
    code = "configuration_error"


class InvalidVerificationCodeError(DomainError):
    status_code = 400
    code = "invalid_verification_code"


class RateLimitError(DomainError):
    status_code = 429
    code = "rate_limited"
