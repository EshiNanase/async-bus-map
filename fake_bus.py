import random
import json
import logging
import os
import sys
from itertools import cycle, islice
import trio
from trio_websocket import open_websocket_url
import argparse
import time
from decorators import relaunch_on_disconnect

logger = logging.getLogger(__name__)


def parse_args():

    parser = argparse.ArgumentParser(description='Fake bus')
    parser.add_argument(
        '--server',
        help='Адрес сервера',
        default='ws://127.0.0.1:8080'
    )
    parser.add_argument(
        '--routes_number',
        help='Количество маршрутов',
        default=500,
        type=int
    )
    parser.add_argument(
        '--buses_per_route',
        help='Количество автобусов на маршруте',
        default=5,
        type=int
    )
    parser.add_argument(
        '--websocket_number',
        help='Количество открытых вебсокетов',
        default=5,
        type=int
    )
    parser.add_argument(
        '--emulator_id',
        help='Префикс к busId на случай запуска нескольких экземпляров',
        default=time.time()
    )
    parser.add_argument(
        '--refresh_timeout',
        help='Задержка в обновлении координат сервера',
        default=1,
        type=int
    )
    parser.add_argument(
        '--verbose',
        help='Показывать логи',
        action='store_true'
    )
    return parser.parse_args()


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(route, start_position, bus_id, refresh_timeout, send_channel):

    cycle_route = route['coordinates'][start_position:] + list(reversed(route['coordinates'][start_position:]))

    for lat, lng in cycle(cycle_route):
        bus = {
            "bus_id": bus_id,
            "lat": lat,
            "lng": lng,
            "route": route['name']
        }

        await send_channel.send(bus)
        await trio.sleep(refresh_timeout)


@relaunch_on_disconnect
async def send_updates(server_address, receive_channel):

    async with open_websocket_url(server_address) as ws:
        async for message in receive_channel:
            await ws.send_message(json.dumps(message, ensure_ascii=True))


async def main():

    args = parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    memory_channels = [trio.open_memory_channel(0) for _ in range(args.websocket_number)]

    async with trio.open_nursery() as nursery:

        for _, receive_channel in memory_channels:
            nursery.start_soon(send_updates, args.server, receive_channel)

        for route in islice(load_routes(), args.routes_number):
            starting_positions = [random.randint(0, len(route['coordinates'])) for _ in range(args.buses_per_route)]

            for starting_position in starting_positions:
                bus_id = f'{route["name"]}-{starting_position}-{args.emulator_id}'
                send_channel, _ = random.choice(memory_channels)
                nursery.start_soon(run_bus, route, starting_position, bus_id, args.refresh_timeout, send_channel)

        logger.info(f'Read {args.routes_number} routes files')
        logger.info(f'Started {args.buses_per_route*args.routes_number} buses in total')


if __name__ == '__main__':
    try:
        trio.run(main)
    except KeyboardInterrupt:
        sys.stderr.write('Вы закрыли скрипт')
