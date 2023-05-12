import random
from itertools import cycle, islice
import trio
import json
import os
from trio_websocket import open_websocket_url


BUSES_PER_ROUTE = 1
CHANNELS_AMOUNT = 1


async def send_updates(server_address, receive_channel):

    print(555)
    while True:
        try:
            print(f'ws://{server_address}/')
            print(123)
            async with open_websocket_url(f'ws://{server_address}/') as ws:
                print(0)
                async with receive_channel:
                    print(1)
                    async for bus in receive_channel:
                        await ws.send_message(json.dumps(bus, ensure_ascii=True))
                        await trio.sleep(1)
        except OSError:
            print('Connection attempt failed: %s')


async def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(route, bus_index, bus_id, send_channel):

    coordinates = cycle(islice(route['coordinates'], bus_index, None))

    while True:

        try:

            for coordinate in coordinates:

                bus = {
                    "busId": bus_id,
                    "lat": coordinate[0],
                    "lng": coordinate[1],
                    "route": route['name']
                }
                await send_channel.send(bus)
                print('лол')
                await trio.sleep(1)

        except StopIteration:

            coordinates = cycle(route['coordinates'])


async def main():

    async with trio.open_nursery() as nursery:
        send_channels = []
        receive_channels = []

        for _ in range(CHANNELS_AMOUNT):
            send_channel, receive_channel = trio.open_memory_channel(0)
            send_channels.append(send_channel)
            receive_channels.append(receive_channel)
            nursery.start_soon(send_updates, '127.0.0.1:8080', receive_channel)

        async for route in load_routes():

            buses_on_route_indexes = [random.randint(0, len(route['coordinates'])) for _ in range(BUSES_PER_ROUTE)]

            for bus_coord in buses_on_route_indexes:
                bus_id = f'{route["name"]}-{bus_coord}'
                nursery.start_soon(run_bus, route, bus_coord, bus_id, random.choice(send_channels))


if __name__ == '__main__':
    trio.run(main)
