from exceptions import BusValidationError


def bus_data_is_valid(bus_data):

    if ('busId', 'route', 'lat', 'lng') not in bus_data:
        raise BusValidationError
