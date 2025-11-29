import os
from dataclasses import dataclass


@dataclass
class Config:
    """Конфигурация приложения"""

    host: str = str(os.getenv('HOST', 'localhost'))
    port: int = int(os.getenv('PORT', '8000'))

    log_to_file: bool = bool(os.getenv('LOG_TO_FILE', 'False'))

    chunk_size: int = int(os.getenv('CHUNK_SIZE', '65536'))  # 64 KB
    max_file_size: int = int(os.getenv('MAX_FILE_SIZE', '1073741824'))  # 1 GB

    connection_timeout: float = float(os.getenv('CONNECTION_TIMEOUT', '30.0'))
    read_timeout: float = float(os.getenv('READ_TIMEOUT', '300.0'))

    min_password_length: int = int(os.getenv('MIN_PASSWORD_LENGTH', '6'))
    max_login_length: int = int(os.getenv('MAX_LOGIN_LENGTH', '50'))
    max_path_length: int = int(os.getenv('MAX_PATH_LENGTH', '4096'))


config = Config()
