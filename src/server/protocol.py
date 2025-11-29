import asyncio
import json
import struct
from typing import Any

from src.utils.config import config
from src.utils.logger import server_logger


class ServerProtocol:
    """Протокол для обработки команд от клиента"""

    @staticmethod
    async def read_json_message(reader) -> dict[str, Any] | None:
        """Читает JSON сообщение из потока"""
        try:
            length_bytes = await reader.readexactly(4)
            length = struct.unpack('>I', length_bytes)[0]

            json_data = await reader.readexactly(length)
            return json.loads(json_data.decode('utf-8'))
        except asyncio.IncompleteReadError:
            return None
        except Exception as e:
            server_logger.error(f'Error reading JSON message: {e}')
            return None

    @staticmethod
    async def read_binary_data(reader, size: int) -> bytes | None:
        """Читает бинарные данные заданного размера"""
        try:
            length_bytes = await reader.readexactly(4)
            data_length = struct.unpack('>I', length_bytes)[0]

            if data_length != size:
                server_logger.warning(f'Несоответствие размера: ожидалось {size}, получено {data_length}')

            data = bytearray()
            remaining = data_length

            while remaining > 0:
                read_size = min(config.chunk_size, remaining)
                chunk = await reader.readexactly(read_size)
                data.extend(chunk)
                remaining -= len(chunk)

            return bytes(data)
        except Exception as e:
            server_logger.error(f'Error reading binary data: {e}')
            return None

    @staticmethod
    async def send_json_message(writer, data: dict[str, Any]):
        """Отправляет JSON сообщение клиенту"""
        try:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            length = len(json_data)

            writer.write(struct.pack('>I', length))
            writer.write(json_data)
            await writer.drain()
        except Exception as e:
            server_logger.error(f'Error sending JSON message: {e}')

    @staticmethod
    async def send_binary_data(writer, data: bytes):
        """Отправляет бинарные данные клиенту"""
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
            server_logger.error(f'Error sending binary data: {e}')

    @staticmethod
    async def send_error(writer, message: str):
        """Отправляет сообщение об ошибке"""
        await ServerProtocol.send_json_message(writer, {'status': 'ERROR', 'message': message})

    @staticmethod
    async def send_ok(writer, data: Any = None):
        """Отправляет успешный ответ"""
        response = {'status': 'OK'}
        if data is not None:
            response['data'] = data
        await ServerProtocol.send_json_message(writer, response)
