import decimal
from typing import Dict
import requests

from flask import current_app

# https://nominatim.org/release-docs/develop/api/Reverse/#other asks for the API user's
# email to be included in the request if a large number of requests is being made
from app.config import WASTE_MANAGEMENT_PROVIDER_NAME

REVERSE_GEOCODE_ENDPOINT = "https://nominatim.openstreetmap.org/reverse?lat={}&lon={}&format=jsonv2"


def nominatim_reverse_geo(lat: decimal, lon: decimal) -> Dict:
    req_url = REVERSE_GEOCODE_ENDPOINT.format(lat, lon)
    assert WASTE_MANAGEMENT_PROVIDER_NAME is not None and WASTE_MANAGEMENT_PROVIDER_NAME != ""
    # Nominatim (reverse geocoding) API User Agent
    # See https://operations.osmfoundation.org/policies/nominatim/
    return requests.get(req_url, headers={'user-agent': WASTE_MANAGEMENT_PROVIDER_NAME}).json().get("address")


def reverse_geocode(lat: decimal, lon: decimal) -> Dict:
    if current_app.config["ENV"] == "production":
        return nominatim_reverse_geo(lat, lon)
    else:
        return {'suburb': 'Theresapark Ward 5', 'village': 'Theresapark Village', 'city': 'Theresapark',
                'county': 'Ehlanzeni', 'state': 'Mpumalanga', 'country': 'South Africa', 'country_code': 'za'}

