import asyncio
import json
import struct
from typing import Any

from src.utils.config import config
from src.utils.exceptions import StorageConnectionError as ConnectionError


class ClientProtocol:
    """Протокол для взаимодействия с сервером"""

    @staticmethod
    async def send_json_message(writer: asyncio.StreamWriter, data: dict[str, Any]) -> None:
        """Отправляет JSON сообщение серверу"""
        try:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            length = len(json_data)

            writer.write(struct.pack('>I', length))
            writer.write(json_data)
            await writer.drain()
        except Exception as e:
            raise ConnectionError(f'Error sending JSON message: {e}') from e

    @staticmethod
    async def send_binary_data(writer: asyncio.StreamWriter, data: bytes) -> None:
        """Отправляет бинарные данные серверу"""
        try:
            writer.write(struct.pack('>I', len(data)))
            await writer.drain()

            offset = 0
            while offset < len(data):
                chunk = data[offset : offset + config.chunk_size]
                writer.write(chunk)
                await writer.drain()
                offset += len(chunk)
        except Exception as e:
            raise ConnectionError(f'Error sending binary data: {e}') from e

    @staticmethod
    async def read_json_message(reader: asyncio.StreamReader) -> dict[str, Any] | None:
        """Читает JSON сообщение из потока"""
        try:
            length_bytes = await reader.readexactly(4)
            length = struct.unpack('>I', length_bytes)[0]

            json_data = await reader.readexactly(length)
            return json.loads(json_data.decode('utf-8'))
        except Exception as e:
            raise ConnectionError(f'Error reading JSON message: {e}') from e

    @staticmethod
    async def read_binary_data(reader: asyncio.StreamReader) -> bytes | None:
        """Читает бинарные данные из потока"""
        try:
            length_bytes = await reader.readexactly(4)
            length = struct.unpack('>I', length_bytes)[0]

            return await reader.readexactly(length)
        except Exception as e:
            raise ConnectionError(f'Error reading binary data: {e}') from e
