import json
import trio
from trio_websocket import serve_websocket, ConnectionClosed
import logging
from functools import partial

BUSES = {}


async def server_8080(request):

    ws = await request.accept()
    while True:
        try:
            bus_data = json.loads(await ws.get_message())
            bus_id = bus_data['busId']
            BUSES[bus_id] = bus_data
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def server_8000(request):
    ws = await request.accept()
    while True:
        try:
            buses_data = {
                "msgType": "Buses",
                "buses": list(BUSES.values())
            }
            await ws.send_message(json.dumps(buses_data))
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def main():
    logging.basicConfig(level=logging.INFO)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, server_8000, '127.0.0.1', 8000, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, server_8080, '127.0.0.1', 8080, ssl_context=None))
        logging.info('servers were started!')


trio.run(main)
