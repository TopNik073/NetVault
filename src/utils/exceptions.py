class StorageError(Exception):
    """Базовое исключение для ошибок хранилища"""

    pass


class StorageConnectionError(StorageError):
    """Ошибка подключения к серверу"""

    pass


class AuthenticationError(StorageError):
    """Ошибка авторизации"""

    pass


class FileError(StorageError):
    """Ошибка при работе с файлом"""

    pass


class ProtocolError(StorageError):
    """Ошибка протокола обмена данными"""

    pass


class ValidationError(StorageError):
    """Ошибка валидации входных данных"""

    pass
