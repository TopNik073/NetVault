import asyncio
from typing import Any
from collections.abc import Callable, Coroutine

from src.server.auth import UserAuth
from src.server.storage import FileStorage
from src.server.protocol import ServerProtocol
from src.utils.config import config
from src.utils.exceptions import ValidationError
from src.utils.logger import server_logger


class Server:
    """Асинхронный TCP сервер для файлового хранилища"""

    def __init__(self):
        self.auth = UserAuth()
        self.storage = FileStorage()
        self.authenticated_users: dict[asyncio.StreamWriter, str] = {}

        self.handlers: dict[
            str, Callable[[dict, asyncio.StreamReader, asyncio.StreamWriter, tuple], Coroutine[Any, Any, None]]
        ] = {
            'REGISTER': self.handle_register,
            'AUTH': self.handle_auth,
            'LOGOUT': self.handle_logout,
            'LIST': self.handle_list,
            'GET': self.handle_get,
            'PUT': self.handle_put,
            'DELETE': self.handle_delete,
            'MOVE': self.handle_move,
        }

    def _get_user_uuid(self, writer: asyncio.StreamWriter) -> str | None:
        """Получает UUID пользователя для соединения"""
        return self.authenticated_users.get(writer)

    def _require_auth(self, writer: asyncio.StreamWriter) -> str:
        """Проверяет авторизацию и возвращает UUID пользователя"""
        user_uuid = self._get_user_uuid(writer)
        if not user_uuid:
            raise ValidationError('Требуется авторизация')
        return user_uuid

    def _validate_input(self, value: str, field_name: str, max_length: int | None = None) -> str:
        """Валидирует входные данные"""
        if not value or not isinstance(value, str):
            raise ValidationError(f'{field_name} обязателен')
        value = value.strip()
        if max_length and len(value) > max_length:
            raise ValidationError(f'{field_name} слишком длинный (максимум {max_length} символов)')
        return value

    async def _execute_handler(
        self, handler: Callable, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Выполняет хендлер с обработкой исключений"""
        try:
            await handler(command, reader, writer, addr)
        except ValidationError as e:
            await ServerProtocol.send_error(writer, str(e))
            server_logger.warning(f'Ошибка валидации: {e}')
        except Exception as e:
            server_logger.error(f'Ошибка в хендлере: {e}', exc_info=True)
            await ServerProtocol.send_error(writer, 'Внутренняя ошибка сервера')

    async def handle_register(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду REGISTER"""
        login = self._validate_input(command.get('login', ''), 'Логин', config.max_login_length)
        password = command.get('password', '')

        if not password or len(password) < config.min_password_length:
            raise ValidationError(f'Пароль должен быть не менее {config.min_password_length} символов')

        user_uuid = self.auth.register_user(login, password)

        if user_uuid:
            await ServerProtocol.send_ok(writer, {'message': 'Пользователь зарегистрирован', 'uuid': user_uuid})
            server_logger.info(f'Зарегистрирован новый пользователь: {login} (UUID: {user_uuid})')
        else:
            await ServerProtocol.send_error(writer, 'Логин уже занят')
            server_logger.warning(f'Попытка регистрации с занятым логином: {login}')

    async def handle_auth(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду AUTH"""
        login = self._validate_input(command.get('login', ''), 'Логин')
        password = command.get('password', '')

        if not password:
            raise ValidationError('Пароль обязателен')

        user_uuid = self.auth.authenticate(login, password)

        if user_uuid:
            self.authenticated_users[writer] = user_uuid
            await ServerProtocol.send_ok(writer, {'message': 'Авторизация успешна'})
            server_logger.info(f'Клиент {addr[0]}:{addr[1]} авторизован как {login}')
        else:
            await ServerProtocol.send_error(writer, 'Неверный логин или пароль')
            server_logger.warning(f'Неудачная попытка авторизации: {login} с {addr[0]}:{addr[1]}')

    async def handle_logout(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду LOGOUT"""
        if writer in self.authenticated_users:
            del self.authenticated_users[writer]
            await ServerProtocol.send_ok(writer, {'message': 'Выход выполнен успешно'})
            server_logger.info(f'Клиент {addr[0]}:{addr[1]} вышел из аккаунта')
        else:
            await ServerProtocol.send_ok(writer, {'message': 'Выход выполнен успешно'})
            server_logger.debug(f'Попытка выхода неавторизованного клиента {addr[0]}:{addr[1]}')

    async def handle_list(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду LIST"""
        user_uuid = self._require_auth(writer)
        path = command.get('path', '')

        files = self.storage.list_files(user_uuid, path)
        await ServerProtocol.send_ok(writer, {'files': files})
        server_logger.debug(f'Список файлов для пользователя {user_uuid}: {len(files)} элементов')

    async def handle_get(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду GET"""
        user_uuid = self._require_auth(writer)
        path = self._validate_input(command.get('path', ''), 'Путь', config.max_path_length)

        file_data = self.storage.get_file(user_uuid, path)
        if file_data is None:
            await ServerProtocol.send_error(writer, 'Файл не найден')
            server_logger.warning(f'Файл не найден: {path} для пользователя {user_uuid}')
        else:
            await ServerProtocol.send_ok(writer, {'filename': path.split('/')[-1], 'size': len(file_data)})
            await ServerProtocol.send_binary_data(writer, file_data)
            server_logger.info(f'Файл отправлен: {path} ({len(file_data)} байт) для пользователя {user_uuid}')

    async def handle_put(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду PUT"""
        user_uuid = self._require_auth(writer)
        path = self._validate_input(command.get('path', ''), 'Путь', config.max_path_length)
        file_size = command.get('size', 0)

        if file_size > config.max_file_size:
            raise ValidationError(f'Файл слишком большой (максимум {config.max_file_size} байт)')

        if file_size <= 0:
            raise ValidationError('Неверный размер файла')

        file_data = await ServerProtocol.read_binary_data(reader, file_size)
        if file_data is None or len(file_data) != file_size:
            raise ValidationError('Ошибка чтения файла')

        if self.storage.put_file(user_uuid, path, file_data):
            await ServerProtocol.send_ok(writer, {'message': 'Файл сохранен'})
            server_logger.info(f'Файл сохранен: {path} ({file_size} байт) для пользователя {user_uuid}')
        else:
            await ServerProtocol.send_error(writer, 'Ошибка сохранения файла')
            server_logger.error(f'Ошибка сохранения файла: {path} для пользователя {user_uuid}')

    async def handle_delete(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду DELETE"""
        user_uuid = self._require_auth(writer)
        path = self._validate_input(command.get('path', ''), 'Путь', config.max_path_length)

        if self.storage.delete_file(user_uuid, path):
            await ServerProtocol.send_ok(writer, {'message': 'Удалено успешно'})
            server_logger.info(f'Удалено: {path} для пользователя {user_uuid}')
        else:
            await ServerProtocol.send_error(writer, 'Ошибка удаления')
            server_logger.warning(f'Ошибка удаления: {path} для пользователя {user_uuid}')

    async def handle_move(
        self, command: dict, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, addr: tuple
    ) -> None:
        """Обрабатывает команду MOVE"""
        user_uuid = self._require_auth(writer)
        source = self._validate_input(command.get('source', ''), 'Исходный путь', config.max_path_length)
        destination = self._validate_input(command.get('destination', ''), 'Путь назначения', config.max_path_length)

        if self.storage.move_file(user_uuid, source, destination):
            await ServerProtocol.send_ok(writer, {'message': 'Перемещено успешно'})
            server_logger.info(f'Перемещено: {source} -> {destination} для пользователя {user_uuid}')
        else:
            await ServerProtocol.send_error(writer, 'Ошибка перемещения: файл не найден')
            server_logger.warning(f'Ошибка перемещения: {source} для пользователя {user_uuid}')

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обрабатывает подключение клиента"""
        addr = writer.get_extra_info('peername')
        server_logger.info(f'Подключился клиент {addr[0]}:{addr[1]}')

        try:
            while True:
                command = await ServerProtocol.read_json_message(reader)
                if not command:
                    break

                cmd_type: str = command.get('command', '').upper()

                if cmd_type not in self.handlers:
                    await ServerProtocol.send_error(writer, f'Неизвестная команда: {cmd_type}')
                    server_logger.warning(f'Неизвестная команда от {addr[0]}:{addr[1]}: {cmd_type}')
                    continue

                handler = self.handlers[cmd_type]
                await self._execute_handler(handler, command, reader, writer, addr)

        except asyncio.IncompleteReadError:
            server_logger.info(f'Клиент {addr[0]}:{addr[1]} отключился')
        except Exception as e:
            server_logger.error(f'Ошибка при обработке клиента {addr[0]}:{addr[1]}: {e}', exc_info=True)
        finally:
            if writer in self.authenticated_users:
                del self.authenticated_users[writer]
            writer.close()
            await writer.wait_closed()
            server_logger.info(f'Соединение с клиентом {addr[0]}:{addr[1]} закрыто')

    async def start(self):
        """Запускает сервер"""
        server = await asyncio.start_server(self.handle_client, config.host, config.port)

        addr = server.sockets[0].getsockname()
        server_logger.info(f'Сервер запущен на {addr[0]}:{addr[1]}')

        async with server:
            await server.serve_forever()


async def server():
    """Точка входа для запуска сервера"""
    s = Server()
    await s.start()
