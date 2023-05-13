import json
import sys
import trio
from trio_websocket import serve_websocket, ConnectionClosed
import logging
from functools import partial
from classes import WindowBounds, Bus
from dataclasses import asdict
import argparse
from exceptions import BusValidationError, NewBoundsValidationError
from tools import bus_data_is_valid

BUSES = {}
window_bounds = WindowBounds()


def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--bus_port',
        help='Порт для имитатора автобусов',
        default=8080,
        type=int
    )
    parser.add_argument(
        '--browser_port',
        help='Порт для браузера',
        default=8000,
        type=int
    )
    parser.add_argument(
        '--verbose',
        help='Показывать логи',
        action='store_true'
    )
    return parser.parse_args()


async def listen_to_updates(request):

    ws = await request.accept()
    while True:
        try:
            bus_data = json.loads(await ws.get_message())
            bus_data_is_valid(bus_data)

            bus_id = bus_data['bus_id']
            bus = Bus(busId=bus_id, route=bus_data['route'], lat=bus_data['lat'], lng=bus_data['lng'])
            BUSES[bus_id] = bus

        except ConnectionClosed:
            await trio.sleep(1)

        except BusValidationError:
            logging.info('BusValidationError!')
            await ws.send_message(json.dumps({
                'msgType': 'Errors',
                'errors': 'Invalid BusMessage'
            }))
            await trio.sleep(5)


async def listen_to_browser_bounds(ws):
    while True:
        try:
            bounds = json.loads(await ws.get_message())
            window_bounds.set_bounds(bounds)

        except ConnectionClosed:
            logging.info('Соединение потеряно! Попытка переподключиться...')
            await trio.sleep(15)

        except NewBoundsValidationError:
            logging.info('NewBoundsValidationError!')
            await ws.send_message(json.dumps({
                'msgType': 'Errors',
                'errors': 'Invalid NewBoundsMessage'
            }))
            await trio.sleep(5)


async def put_buses_on_map(ws):
    while True:
        try:
            buses_on_map = [asdict(BUSES[bus]) for bus in BUSES if window_bounds.is_inside(BUSES[bus])]
            logging.info(f'{len(buses_on_map)} buses are visible')
            buses_data = {
                "msgType": "Buses",
                "buses": buses_on_map
            }
            await ws.send_message(json.dumps(buses_data))
            await trio.sleep(1)

        except ConnectionClosed:
            logging.info('Соединение потеряно! Попытка переподключиться...')
            await trio.sleep(15)


async def talk_to_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(put_buses_on_map, ws)
        nursery.start_soon(listen_to_browser_bounds, ws)


async def main():

    args = parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, talk_to_browser, '127.0.0.1', args.browser_port, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, listen_to_updates, '127.0.0.1', args.bus_port, ssl_context=None))
        logging.info('servers were started!')


if __name__ == '__main__':
    try:
        trio.run(main)
    except KeyboardInterrupt:
        sys.stderr.write('Вы закрыли скрипт')
