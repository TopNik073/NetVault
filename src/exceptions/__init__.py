import logging

class BaseServerError(Exception):
    level = logging.NOTSET
    http_code: int
    message: str | None
    code: str | None

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        level: int | None = None,
        http_code: int | None = None,
    ):
        super().__init__(message)
        self.message = message or self.message
        self.code = code or self.code
        self.level = level or self.level
        self.http_code = http_code or self.http_code


class ServerError(BaseServerError):
    level = logging.ERROR
    http_code = 500


class ClientError(BaseServerError):
    level = logging.WARNING
    http_code = 400


class NotFound(ClientError):
    http_code = 404
    code = 'not_found'
    message = 'The requested resource is not found'


class PermissionDenied(ClientError):
    http_code = 403
    code = 'permission_denied'
    message = 'Insufficient permissions'

class Conflict(ClientError):
    http_code = 409
    code = 'conflict'
    message = 'The conflict was occurred while processing the request'

class RedisException(ClientError):
    level = logging.ERROR
    http_code = 500
    code = 'redis_exception'
    message = 'Redis server error'

# --------- AUTH ---------
class EmailAlreadyExists(ClientError):
    code = "email_exists"
    message = "User with this email already exists"
    http_code = 409

class InvalidCredentials(ClientError):
    code = "invalid_credentials"
    message = "Invalid email or password"

class SessionExpired(ClientError):
    code = "session_expired"
    message = "Session expired or not found"

class InvalidSessionData(ClientError):
    code = "invalid_session_data"
    message = "Invalid session data"

class InvalidCode(ClientError):
    code = "invalid_code"
    message = "Invalid verification code"

class CodeExpired(ClientError):
    code = "code_expired"
    message = "Code expired"

class InvalidSessionType(ClientError):
    code = "invalid_session_type"
    message = "Invalid session type"

class InvalidToken(ClientError):
    code = "invalid_token"
    message = "Invalid or expired token"