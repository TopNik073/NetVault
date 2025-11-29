import json
import uuid
from pathlib import Path
from typing import Any

from src.utils.constants import USERS_FILE
from src.utils.security import hash_password, verify_password


class UserAuth:
    """Класс для управления авторизацией пользователей"""

    def __init__(self, users_file: Path = USERS_FILE):
        self.users_file = users_file
        self._ensure_users_file()

    def _ensure_users_file(self):
        """Создает файл users.json, если его нет"""
        if not self.users_file.exists():
            self._save_users({})

    def _load_users(self) -> dict[str, Any]:
        """Загружает пользователей из JSON файла"""
        try:
            if not self.users_file.exists():
                return {}
            with self.users_file.open(encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_users(self, users: dict[str, Any]):
        """Сохраняет пользователей в JSON файл"""
        with self.users_file.open('w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def register_user(self, login: str, password: str) -> str | None:
        """Регистрирует нового пользователя. Возвращает UUID или None, если логин занят"""
        users = self._load_users()

        for user_data in users.values():
            if user_data.get('login') == login:
                return None

        user_uuid = str(uuid.uuid4())
        users[user_uuid] = {'login': login, 'password_hash': hash_password(password)}

        self._save_users(users)
        return user_uuid

    def authenticate(self, login: str, password: str) -> str | None:
        """Аутентифицирует пользователя. Возвращает UUID или None"""
        users = self._load_users()

        for user_uuid, user_data in users.items():
            if user_data.get('login') == login and verify_password(password, user_data.get('password_hash', '')):
                return user_uuid

        return None

    def get_user_uuid(self, login: str) -> str | None:
        """Получает UUID пользователя по логину"""
        users = self._load_users()

        for user_uuid, user_data in users.items():
            if user_data.get('login') == login:
                return user_uuid

        return None
