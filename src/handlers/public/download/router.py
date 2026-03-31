from pathlib import Path
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

download_router = APIRouter(prefix='/download')

TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / 'templates' / 'download_page.html'


def _load_template(link_id: str) -> str:
    template = TEMPLATE_PATH.read_text()
    return template.replace('{{link_id}}', link_id)


@download_router.get('/{link_id}', response_class=HTMLResponse)
async def public_download_page(link_id: UUID):
    return _load_template(str(link_id))
