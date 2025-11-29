from typing import TypedDict, Literal


class FileInfo(TypedDict):
    """Информация о файле или директории"""

    name: str
    type: Literal['file', 'directory']
    size: int


class CommandResponse(TypedDict, total=False):
    """Ответ сервера на команду"""

    status: Literal['OK', 'ERROR']
    message: str
    data: dict
    files: list[FileInfo]
    filename: str
    size: int
    uuid: str


class CommandRequest(TypedDict, total=False):
    """Запрос команды к серверу"""

    command: Literal['REGISTER', 'AUTH', 'LIST', 'GET', 'PUT', 'DELETE']
    login: str
    password: str
    path: str
    size: int
