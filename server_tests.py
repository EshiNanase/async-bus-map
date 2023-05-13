import pytest
import trio
from trio_websocket import open_websocket_url
import json


@pytest.mark.asyncio
async def test_invalid_new_bounds():

    bad_msg_type = {
        'msgType': 'notnewBounds',
        'data': {
            'east_lng': 0,
            'west_lng': 0,
            'north_lat': 0,
            'south_lat': 0
        }
    }
    bad_data = {
        'msgType': 'newBounds',
        'data': {
            'east1_lng': 0,
            'west_lng': 0,
            'north_lat': 0,
            'south_lat': 0
        }
    }
    bad_msg_response = '{"msgType": "Errors", "errors": "Invalid NewBoundsMessage"}'

    async def trio_function():

        async with open_websocket_url('ws://127.0.0.1:8000') as ws:

            await ws.send_message(json.dumps(bad_msg_type, ensure_ascii=True))
            for _ in range(10):
                response = await ws.get_message()
                if 'Errors' in response:
                    assert response == bad_msg_response

            await ws.send_message(json.dumps(bad_data, ensure_ascii=True))
            for _ in range(10):
                response = await ws.get_message()
                if 'Errors' in response:
                    assert response == bad_msg_response

    trio.run(trio_function)


@pytest.mark.asyncio
async def test_invalid_bus():

    bad_data = {
        'busId': '123',
        'lat': 123,
        'lng': 123,
        'routee': '123'
    }
    bad_msg_response = '{"msgType": "Errors", "errors": "Invalid BusMessage"}'

    async def trio_function():

        async with open_websocket_url('ws://127.0.0.1:8080') as ws:

            await ws.send_message(json.dumps(bad_data, ensure_ascii=True))
            response = await ws.get_message()
            assert response == bad_msg_response

    trio.run(trio_function)
