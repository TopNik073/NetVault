import asyncio
import sys
import traceback

import click

from src.server import server
from src.client.cli import cli


async def run_server():
    """Запускает сервер"""
    await server()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        try:
            asyncio.run(run_server())
        except KeyboardInterrupt:
            click.echo('\nСервер отключен')
        except Exception:
            traceback.print_exc()
    else:
        cli()
