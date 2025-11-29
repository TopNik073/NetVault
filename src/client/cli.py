import click
import asyncio
import atexit
import shlex

from src.client.client import FileStorageClient
import contextlib


_client = None
_loop = None


def get_event_loop():
    """Получает или создает event loop"""
    global _loop
    try:
        _loop = asyncio.get_event_loop()
        if _loop.is_closed():
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
    except RuntimeError:
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def get_client() -> FileStorageClient:
    """Получает глобальный экземпляр клиента"""
    global _client
    if _client is None:
        _client = FileStorageClient()
        atexit.register(cleanup_client)
    return _client


def cleanup_client():
    """Закрывает соединение при выходе из программы"""
    global _client, _loop
    if _client and _loop and not _loop.is_closed():
        with contextlib.suppress(Exception):
            _loop.run_until_complete(_client.disconnect())


def run_async(coro):
    """Запускает корутину в глобальном event loop"""
    loop = get_event_loop()
    if loop.is_running():
        return asyncio.run(coro)
    return loop.run_until_complete(coro)


def ensure_authenticated(client: FileStorageClient, login: str | None = None, password: str | None = None) -> bool:
    """Обеспечивает авторизацию клиента. Если передан login и password, выполняет авторизацию"""
    if login and password:
        result = run_async(client.login(login, password))
        if not result:
            click.echo('Ошибка авторизации', err=True)
            return False
        return True
    if not client.authenticated:
        click.echo('Требуется авторизация. Используйте команду login или передайте --login и --password.', err=True)
        return False
    return True


@click.group()
def cli():
    """CLI клиент для файлового хранилища"""
    pass


@cli.command()
@click.option('--login', prompt='Логин', help='Логин пользователя')
@click.option('--password', prompt='Пароль', hide_input=True, help='Пароль пользователя')
def register(login: str, password: str):
    """Регистрирует нового пользователя на сервере"""
    client = get_client()
    result = run_async(client.register(login, password))
    if result:
        click.echo('Регистрация успешна')
    else:
        click.echo('Ошибка регистрации', err=True)


@cli.command()
@click.option('--login', prompt='Логин', help='Логин пользователя')
@click.option('--password', prompt='Пароль', hide_input=True, help='Пароль пользователя')
def login(login: str, password: str):
    """Авторизуется на сервере"""
    client = get_client()
    result = run_async(client.login(login, password))
    if result:
        click.echo('Авторизация успешна')
    else:
        click.echo('Ошибка авторизации', err=True)


@cli.command()
@click.argument('path', required=False, default='')
@click.option('--login', help='Логин для авторизации (если не авторизован)')
@click.option('--password', help='Пароль для авторизации (если не авторизован)')
def list(path: str, login: str | None, password: str | None):
    """Выводит список файлов и папок"""
    client = get_client()
    if not ensure_authenticated(client, login, password):
        return

    files = run_async(client.list_files(path))
    if files is not None:
        if not files:
            click.echo('Папка пуста')
        else:
            for item in files:
                item_type = '📁' if item['type'] == 'directory' else '📄'
                size = f' ({item["size"]} байт)' if item['type'] == 'file' else ''
                click.echo(f'{item_type} {item["name"]}{size}')


@cli.command()
@click.argument('remote_path')
@click.argument('local_path')
@click.option('--login', help='Логин для авторизации (если не авторизован)')
@click.option('--password', help='Пароль для авторизации (если не авторизован)')
def get(remote_path: str, local_path: str, login: str | None, password: str | None):
    """Скачивает файл с сервера"""
    client = get_client()
    if not ensure_authenticated(client, login, password):
        return
    run_async(client.get_file(remote_path, local_path))


@cli.command()
@click.argument('local_path')
@click.argument('remote_path')
@click.option('--login', help='Логин для авторизации (если не авторизован)')
@click.option('--password', help='Пароль для авторизации (если не авторизован)')
def put(local_path: str, remote_path: str, login: str | None, password: str | None):
    """Загружает файл на сервер"""
    client = get_client()
    if not ensure_authenticated(client, login, password):
        return
    run_async(client.put_file(local_path, remote_path))


@cli.command()
@click.argument('path')
@click.option('--login', help='Логин для авторизации (если не авторизован)')
@click.option('--password', help='Пароль для авторизации (если не авторизован)')
def delete(path: str, login: str | None, password: str | None):
    """Удаляет файл или директорию на сервере"""
    client = get_client()
    if not ensure_authenticated(client, login, password):
        return
    run_async(client.delete_file(path))


@cli.command()
def interactive():
    """Запускает интерактивный режим (соединение сохраняется между командами)"""
    click.echo("Интерактивный режим. Введите 'help' для справки, 'exit' для выхода.")

    client = get_client()

    while True:
        try:
            line = input('> ').strip()
            if not line:
                continue

            if line.lower() in ['exit', 'quit', 'q']:
                click.echo('Выход...')
                run_async(client.disconnect())
                break

            parts = shlex.split(line)
            if not parts:
                continue

            cmd = parts[0]
            args = parts[1:]

            MIN_LOGIN_ARGS = 2
            if cmd == 'login':
                if len(args) >= MIN_LOGIN_ARGS:
                    login, password = args[0], args[1]
                    result = run_async(client.login(login, password))
                    click.echo('Авторизация успешна' if result else 'Ошибка авторизации', err=not result)
                else:
                    click.echo('Использование: login <логин> <пароль>', err=True)

            elif cmd == 'register':
                if len(args) >= MIN_LOGIN_ARGS:
                    result = run_async(client.register(args[0], args[1]))
                    click.echo('Регистрация успешна' if result else 'Ошибка регистрации', err=not result)
                else:
                    click.echo('Использование: register <логин> <пароль>', err=True)

            elif cmd == 'logout':
                result = run_async(client.logout())
                click.echo('Выход выполнен' if result else 'Ошибка выхода', err=not result)

            elif cmd == 'list':
                path = args[0] if args else ''
                files = run_async(client.list_files(path))
                if files is not None:
                    if not files:
                        click.echo('Папка пуста')
                    else:
                        for item in files:
                            item_type = '📁 ' if item['type'] == 'directory' else '📄 '
                            size = f' ({item["size"]} байт)' if item['type'] == 'file' else ''
                            click.echo(f'{item_type} {item["name"]}{size}')

            elif cmd == 'get':
                if len(args) >= MIN_LOGIN_ARGS:
                    run_async(client.get_file(args[0], args[1]))
                else:
                    click.echo('Использование: get <remote_path> <local_path>', err=True)

            elif cmd == 'put':
                if len(args) >= MIN_LOGIN_ARGS:
                    run_async(client.put_file(args[0], args[1]))
                else:
                    click.echo('Использование: put <local_path> <remote_path>', err=True)

            elif cmd == 'delete':
                if args:
                    run_async(client.delete_file(args[0]))
                else:
                    click.echo('Использование: delete <path>', err=True)

            elif cmd == 'help':
                click.echo("""
Доступные команды:
  login <логин> <пароль>    - Авторизация
  register <логин> <пароль>  - Регистрация
  logout                    - Выход из аккаунта
  list [path]                - Список файлов
  get <remote> <local>       - Скачать файл
  put <local> <remote>       - Загрузить файл
  delete <path>              - Удалить файл/папку
  exit                       - Выход
                """)

            else:
                click.echo(f"Неизвестная команда: {cmd}. Введите 'help' для справки.", err=True)

        except KeyboardInterrupt:
            click.echo('\nВыход...')
            run_async(client.disconnect())
            break
        except EOFError:
            click.echo('\nВыход...')
            run_async(client.disconnect())
            break
        except Exception as e:
            click.echo(f'Ошибка: {e}', err=True)


if __name__ == '__main__':
    cli()
