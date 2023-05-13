import trio
import trio_websocket
import logging
from functools import wraps


def relaunch_on_disconnect(async_func):
    @wraps(async_func)
    async def wrapper(*args, **kwargs):
        while True:
            try:
                return await async_func(*args, **kwargs)
            except (trio_websocket.ConnectionClosed, trio_websocket.HandshakeError):
                logging.info('Соединение закрыто! Попытка переподключения...')
                await trio.sleep(5)
    return wrapper
