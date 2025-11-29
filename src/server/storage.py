import shutil
from pathlib import Path
from typing import Any

from src.utils.constants import STORAGE_DIR
from src.utils.config import config
from src.utils.exceptions import ValidationError
from src.utils.logger import server_logger


class FileStorage:
    """Класс для управления файловым хранилищем пользователей"""

    def __init__(self, storage_dir: Path = STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get_user_dir(self, user_uuid: str) -> Path:
        """Возвращает путь к директории пользователя"""
        user_dir = self.storage_dir / user_uuid
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _resolve_path(self, user_uuid: str, path: str) -> Path:
        """Разрешает путь относительно директории пользователя"""
        if not path:
            return self.get_user_dir(user_uuid)

        if len(path) > config.max_path_length:
            raise ValidationError(f'Путь слишком длинный (максимум {config.max_path_length} символов)')

        user_dir = self.get_user_dir(user_uuid)

        normalized_path = path.lstrip('/')
        normalized_path = normalized_path.replace('../', '').replace('..\\', '')
        if '..' in normalized_path:
            raise ValidationError('Path traversal detected')

        if normalized_path.startswith('/') or '\\' in normalized_path:
            raise ValidationError('Недопустимые символы в пути')

        resolved = (user_dir / normalized_path).resolve()

        try:
            resolved.relative_to(user_dir.resolve())
        except ValueError as e:
            raise ValidationError('Path traversal detected') from e

        return resolved

    def list_files(self, user_uuid: str, path: str = '') -> list[dict[str, Any]]:
        """Возвращает список файлов и папок в указанном пути"""
        try:
            target_path = self._resolve_path(user_uuid, path)

            if not target_path.exists():
                return []

            if target_path.is_file():
                return [{'name': target_path.name, 'type': 'file', 'size': target_path.stat().st_size}]

            items = []
            for item in target_path.iterdir():
                items.append(
                    {
                        'name': item.name,
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': item.stat().st_size if item.is_file() else 0,
                    }
                )

            return sorted(items, key=lambda x: (x['type'] == 'file', x['name']))
        except (ValidationError, ValueError) as e:
            raise ValidationError(f'Error listing files: {e!s}') from e
        except Exception as e:
            server_logger.error(f'Неожиданная ошибка при получении списка файлов: {e}')
            raise ValueError(f'Error listing files: {e!s}') from e

    def get_file(self, user_uuid: str, path: str) -> bytes | None:
        """Читает файл и возвращает его содержимое"""
        try:
            file_path = self._resolve_path(user_uuid, path)

            if not file_path.exists() or not file_path.is_file():
                return None

            with file_path.open('rb') as f:
                return f.read()
        except Exception:
            return None

    def put_file(self, user_uuid: str, path: str, data: bytes) -> bool:
        """Записывает файл в хранилище"""
        try:
            if len(data) > config.max_file_size:
                raise ValidationError(f'Файл слишком большой (максимум {config.max_file_size} байт)')

            file_path = self._resolve_path(user_uuid, path)

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open('wb') as f:
                f.write(data)

            return True
        except (ValidationError, ValueError) as e:
            server_logger.warning(f'Ошибка валидации при сохранении файла: {e}')
            return False
        except Exception as e:
            server_logger.error(f'Ошибка при сохранении файла: {e}')
            return False

    def delete_file(self, user_uuid: str, path: str) -> bool:
        """Удаляет файл или директорию"""
        try:
            target_path = self._resolve_path(user_uuid, path)

            if not target_path.exists():
                return False

            if target_path.is_file():
                target_path.unlink()
            elif target_path.is_dir():
                shutil.rmtree(target_path)

            return True
        except Exception:
            return False

    def move_file(self, user_uuid: str, source_path: str, destination_path: str) -> bool:
        """Перемещает или переименовывает файл или директорию"""
        try:
            source = self._resolve_path(user_uuid, source_path)
            destination = self._resolve_path(user_uuid, destination_path)

            if not source.exists():
                return False

            if destination.exists():
                raise ValidationError('Файл назначения уже существует')

            destination.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(source), str(destination))

            return True
        except ValidationError:
            raise
        except Exception as e:
            server_logger.error(f'Ошибка при перемещении файла: {e}')
            return False
