from exceptions import BusValidationError


def is_valid_bus_data(bus_data):

    valid_keys = ['bus_id', 'lat', 'lng', 'route']

    if valid_keys != list(bus_data.keys()):
        raise BusValidationError
