import uvicorn

from src.app_factory import AppFactory
from src.core.config import config
from src.handlers import ROUTERS
from src.middlewares import MIDDLEWARES

if __name__ == '__main__':
    app = AppFactory(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        debug=config.DEBUG,
        lifespan=None,
        routers=ROUTERS,
        middlewares=MIDDLEWARES,
    )

    uvicorn.run(app.app, host=config.APP_HOST, port=config.APP_PORT, log_level='critical')