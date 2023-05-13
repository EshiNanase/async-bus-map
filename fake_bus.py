import random
import json
import logging
import os
from itertools import cycle
import trio
from trio_websocket import open_websocket_url

BUSES_PER_ROUTE = 25
CHANNELS_AMOUNT = 10

logger = logging.getLogger(__name__)


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(route, start_position, bus_id, send_channel):

    cycle_route = route['coordinates'][start_position:] + list(reversed(route['coordinates'][start_position:]))

    for lat, lng in cycle(cycle_route):
        bus = {
            "busId": bus_id,
            "lat": lat,
            "lng": lng,
            "route": route['name']
        }

        await send_channel.send(bus)
        await trio.sleep(1)


async def send_updates(server_address, receive_channel):

    while True:
        async with open_websocket_url(server_address) as ws:
            async for message in receive_channel:
                await ws.send_message(json.dumps(message, ensure_ascii=True))


async def main():

    logging.basicConfig(level=logging.INFO)

    memory_channels = [trio.open_memory_channel(0) for _ in range(CHANNELS_AMOUNT)]

    async with trio.open_nursery() as nursery:

        for _, receive_channel in memory_channels:
            nursery.start_soon(send_updates, 'ws://127.0.0.1:8080', receive_channel)

        for route in load_routes():
            starting_positions = [random.randint(0, len(route['coordinates'])) for _ in range(BUSES_PER_ROUTE)]
            for starting_position in starting_positions:
                bus_id = f'{route["name"]}-{starting_position}'
                send_channel, _ = random.choice(memory_channels)
                nursery.start_soon(run_bus, route, starting_position, bus_id, send_channel)

        logger.info(f'Read 900 routes files')
        logger.info(f'Started {BUSES_PER_ROUTE*900} buses in total')


if __name__ == '__main__':
    trio.run(main)
