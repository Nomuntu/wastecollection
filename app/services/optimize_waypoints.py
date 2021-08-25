from typing import List, Tuple, Union

import requests
from sys import stderr

import app.config as config
from app.model import CollectionRequest

OPTIMIZE_WAYPOINTS_URL = \
    'https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&waypoints=optimize:true|{}&key={}'

DIRECTIONS_URL_NO_ORIGIN = \
    'https://www.google.com/maps/dir/?api=1&destination={}&waypoints={}'


def optimize_waypoints(reqs: List[CollectionRequest]) -> Tuple[bool, List[CollectionRequest], Union[str, None]]:
    api_key = config.GCP_API_KEY

    if api_key is None:
        print(f'Missing GCP API KEY – trip waypoints will not be optimized', file=stderr)
        return False, reqs, 'Missing Google Cloud Platform API Key'

    origin = f'{config.HQ_COORDS[0]},{config.HQ_COORDS[1]}'
    destination = origin
    waypoints = '|'.join([f'{req.location_lat},{req.location_lon}' for req in reqs])

    url = OPTIMIZE_WAYPOINTS_URL.format(origin, destination, waypoints, api_key)
    print(f'getting {url}')

    response = requests.get(url)
    response_json = response.json()

    if (status := response_json['status']) != 'OK':
        print(f'response status: {status}', file=stderr)

        err_msg = response_json.get('error_message')
        print(f'error message: {err_msg}', file=stderr)

        return False, reqs, f'[{status}] {err_msg}'

    waypoint_order = response_json['routes'][0]['waypoint_order']

    print("waypoint_order:")
    print(waypoint_order)

    optimized_reqs = [reqs[i] for i in waypoint_order]

    return True, optimized_reqs, None


def trip_maps_url(reqs: List[CollectionRequest]) -> str:
    destination = f'{reqs[-1].location_lat},{reqs[-1].location_lon}'
    waypoints = '|'.join([f'{req.location_lat},{req.location_lon}' for req in reqs[0 : -1]])

    return DIRECTIONS_URL_NO_ORIGIN.format(destination, waypoints)

