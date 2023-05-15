from dataclasses import dataclass
import json
from exceptions import NewBoundsValidationError, BusValidationError


class WindowBounds:

    def __init__(self):

        self.south_lat = 0
        self.north_lat = 0
        self.west_lng = 0
        self.east_lng = 0

    def is_inside(self, bus):

        if self.south_lat < bus.lat < self.north_lat and self.west_lng < bus.lng < self.east_lng:
            return True

    def set_bounds(self, bounds):

        valid_keys = ['south_lat', 'north_lat', 'west_lng', 'east_lng']
        if bounds.get('msgType') != 'newBounds':
            raise NewBoundsValidationError
        if valid_keys != list(bounds['data'].keys()):
            raise NewBoundsValidationError

        self.south_lat = bounds['data']['south_lat']
        self.north_lat = bounds['data']['north_lat']
        self.west_lng = bounds['data']['west_lng']
        self.east_lng = bounds['data']['east_lng']


@dataclass
class Bus:

    busId: str
    route: str
    lat: float
    lng: float
