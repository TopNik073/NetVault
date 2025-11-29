import asyncio
from pathlib import Path

import click

from src.client.protocol import ClientProtocol
from src.utils.config import config
from src.utils.exceptions import StorageConnectionError, AuthenticationError, FileError
from src.utils.logger import client_logger


class FileStorageClient:
    """Клиент для работы с файловым хранилищем"""

    def __init__(self):
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.authenticated = False

    async def connect(self) -> bool:
        """Подключается к серверу"""
        if self.writer and not self.writer.is_closing():
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

        try:
            self.reader, self.writer = await asyncio.open_connection(config.host, config.port)
            self.authenticated = False
            client_logger.info(f'Подключено к серверу {config.host}:{config.port}')
            return True
        except Exception as e:
            client_logger.error(f'Ошибка подключения: {e}')
            click.echo(f'Ошибка подключения: {e}', err=True)
            self.reader = None
            self.writer = None
            return False

    def _ensure_connected(self) -> bool:
        """Проверяет, что соединение активно"""
        return self.reader is not None and self.writer is not None and not self.writer.is_closing()

    async def _ensure_connection(self) -> bool:
        """Проверяет и переподключается, если соединение потеряно"""
        if not self._ensure_connected():
            client_logger.info('Не обнаружено активных соединений, подключаюсь...')
            if not await self.connect():
                raise StorageConnectionError('Не удалось подключиться к серверу')
        return True

    def _require_auth(self):
        """Проверяет, что пользователь авторизован"""
        if not self.authenticated:
            raise AuthenticationError('Требуется авторизация. Используйте команду login.')

    async def disconnect(self):
        """Отключается от сервера"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.authenticated = False

    async def register(self, login: str, password: str) -> bool:
        """Регистрирует нового пользователя на сервере"""
        try:
            await self._ensure_connection()

            await ClientProtocol.send_json_message(
                self.writer, {'command': 'REGISTER', 'login': login, 'password': password}
            )

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                client_logger.info(f'Пользователь {login} зарегистрирован')
                return True
            error_msg = response.get('message', 'Ошибка регистрации') if response else 'Ошибка регистрации'
            client_logger.warning(f'Ошибка регистрации: {error_msg}')
            click.echo(f'Ошибка: {error_msg}', err=True)
            return False
        except StorageConnectionError as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при регистрации: {e}')
            click.echo(f'Ошибка при регистрации: {e}', err=True)
            return False

    async def login(self, login: str, password: str) -> bool:
        """Авторизуется на сервере"""
        try:
            await self._ensure_connection()

            await ClientProtocol.send_json_message(
                self.writer, {'command': 'AUTH', 'login': login, 'password': password}
            )

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                self.authenticated = True
                client_logger.info(f'Пользователь {login} авторизован')
                return True
            error_msg = response.get('message', 'Ошибка авторизации') if response else 'Ошибка авторизации'
            client_logger.warning(f'Ошибка авторизации: {error_msg}')
            click.echo(f'Ошибка: {error_msg}', err=True)
            return False
        except StorageConnectionError as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при авторизации: {e}')
            click.echo(f'Ошибка при авторизации: {e}', err=True)
            return False

    async def logout(self) -> bool:
        """Выходит из аккаунта на сервере"""
        try:
            await self._ensure_connection()

            await ClientProtocol.send_json_message(self.writer, {'command': 'LOGOUT'})

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                self.authenticated = False
                client_logger.info('Выход из аккаунта выполнен')
                return True
            error_msg = response.get('message', 'Ошибка выхода') if response else 'Ошибка выхода'
            client_logger.warning(f'Ошибка выхода: {error_msg}')
            click.echo(f'Ошибка: {error_msg}', err=True)
            return False
        except StorageConnectionError as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при выходе: {e}')
            click.echo(f'Ошибка при выходе: {e}', err=True)
            return False

    async def list_files(self, path: str = '') -> list | None:
        """Получает список файлов"""
        try:
            await self._ensure_connection()
            self._require_auth()

            await ClientProtocol.send_json_message(self.writer, {'command': 'LIST', 'path': path})

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                files = response.get('data', {}).get('files', [])
                client_logger.debug(f'Получен список файлов: {len(files)} элементов')
                return files
            error_msg = response.get('message', 'Ошибка') if response else 'Ошибка'
            client_logger.warning(f'Ошибка получения списка файлов: {error_msg}')
            click.echo(f'Ошибка: {error_msg}', err=True)
            return None
        except (StorageConnectionError, AuthenticationError) as e:
            click.echo(str(e), err=True)
            return None
        except Exception as e:
            client_logger.error(f'Ошибка при получении списка файлов: {e}')
            click.echo(f'Ошибка при получении списка файлов: {e}', err=True)
            return None

    async def get_file(self, remote_path: str, local_path: str) -> bool:
        """Скачивает файл с сервера"""
        try:
            await self._ensure_connection()
            self._require_auth()

            await ClientProtocol.send_json_message(self.writer, {'command': 'GET', 'path': remote_path})

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                file_size = response.get('data', {}).get('size', 0)
                client_logger.info(f'Скачивание файла {remote_path} ({file_size} байт)')

                if file_size > 1024 * 512:
                    with click.progressbar(length=file_size, label='Скачивание') as bar:
                        file_data = await ClientProtocol.read_binary_data(self.reader)
                        if file_data:
                            bar.update(len(file_data))
                else:
                    file_data = await ClientProtocol.read_binary_data(self.reader)

                if file_data:
                    local_file = Path(local_path).expanduser()
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    local_file.write_bytes(file_data)
                    client_logger.info(f'Файл сохранен: {local_path}')
                    click.echo(f'Файл сохранен: {local_path}')
                    return True
                raise FileError('Не удалось получить данные файла')
            error_msg = response.get('message', 'Ошибка') if response else 'Ошибка'
            raise FileError(error_msg)
        except (StorageConnectionError, AuthenticationError, FileError) as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при получении файла: {e}')
            click.echo(f'Ошибка при получении файла: {e}', err=True)
            return False

    async def put_file(self, local_path: str, remote_path: str) -> bool:
        """Загружает файл на сервер"""
        try:
            await self._ensure_connection()
            self._require_auth()

            local_file = Path(local_path).expanduser()
            if not local_file.exists():
                raise FileError(f'Файл не найден: {local_path}')

            file_size = local_file.stat().st_size
            if file_size > config.max_file_size:
                raise FileError(f'Файл слишком большой: {file_size} байт (максимум: {config.max_file_size})')

            client_logger.info(f'Загрузка файла {local_path} -> {remote_path} ({file_size} байт)')

            file_data = local_file.read_bytes()

            await ClientProtocol.send_json_message(
                self.writer, {'command': 'PUT', 'path': remote_path, 'size': len(file_data)}
            )

            if file_size > 1024 * 512:
                with click.progressbar(length=file_size, label='Загрузка') as bar:
                    await ClientProtocol.send_binary_data(self.writer, file_data)
                    bar.update(file_size)
            else:
                await ClientProtocol.send_binary_data(self.writer, file_data)

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                client_logger.info(f'Файл загружен: {remote_path}')
                click.echo(f'Файл загружен: {remote_path}')
                return True
            error_msg = response.get('message', 'Ошибка') if response else 'Ошибка'
            raise FileError(error_msg)
        except (StorageConnectionError, AuthenticationError, FileError) as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при загрузке файла: {e}')
            click.echo(f'Ошибка при загрузке файла: {e}', err=True)
            return False

    async def delete_file(self, path: str) -> bool:
        """Удаляет файл или директорию на сервере"""
        try:
            await self._ensure_connection()
            self._require_auth()

            client_logger.info(f'Удаление: {path}')
            await ClientProtocol.send_json_message(self.writer, {'command': 'DELETE', 'path': path})

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                client_logger.info(f'Удалено: {path}')
                click.echo(f'Удалено: {path}')
                return True
            error_msg = response.get('message', 'Ошибка') if response else 'Ошибка'
            raise FileError(error_msg)
        except (StorageConnectionError, AuthenticationError, FileError) as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при удалении: {e}')
            click.echo(f'Ошибка при удалении: {e}', err=True)
            return False

    async def move_file(self, source_path: str, destination_path: str) -> bool:
        """Перемещает или переименовывает файл или директорию на сервере"""
        try:
            await self._ensure_connection()
            self._require_auth()

            client_logger.info(f'Перемещение: {source_path} -> {destination_path}')
            await ClientProtocol.send_json_message(
                self.writer, {'command': 'MOVE', 'source': source_path, 'destination': destination_path}
            )

            response = await ClientProtocol.read_json_message(self.reader)
            if response and response.get('status') == 'OK':
                client_logger.info(f'Перемещено: {source_path} -> {destination_path}')
                click.echo(f'Перемещено: {source_path} -> {destination_path}')
                return True
            error_msg = response.get('message', 'Ошибка') if response else 'Ошибка'
            raise FileError(error_msg)
        except (StorageConnectionError, AuthenticationError, FileError) as e:
            click.echo(str(e), err=True)
            return False
        except Exception as e:
            client_logger.error(f'Ошибка при перемещении: {e}')
            click.echo(f'Ошибка при перемещении: {e}', err=True)
            return False
