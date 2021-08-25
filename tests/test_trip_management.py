import datetime
import string
import random

import bcrypt
import pytest
import json

from decimal import Decimal
from app.model import Trip, CollectionRequestStatus, CollectionRequest, Employee, EmployeeRole
from tests.conftest import successful


@pytest.fixture
def requests(db):
    req1 = CollectionRequest(collector_name='Spongebob', collector_phone='0812222222', location_lat=Decimal('1.22'),
                             location_lon=Decimal('2.22'), waste_entries=[])

    req2 = CollectionRequest(collector_name='Patrick', collector_phone='0812222222', location_lat=Decimal('1.22'),
                             location_lon=Decimal('2.22'), waste_entries=[])

    req3 = CollectionRequest(collector_name='Squidward', collector_phone='0812222222', location_lat=Decimal('1.22'),
                             location_lon=Decimal('2.22'), waste_entries=[])
    db.session.add(req1)
    db.session.add(req2)
    db.session.add(req3)
    db.session.commit()

    return [req1, req2, req3]


def create_trip(testapp, reqIds):
    json = {
        'tripId': 'new_trip',
        'reqIds': reqIds
    }

    return testapp.post(f'/api/admin/add_to_trip', json=json)


def test_new_admin_trip_creation(testapp, requests):
    all_req_ids_in_trips = [collection.id for trip in Trip.query.all() for collection in trip.collections]
    for req in requests:
        assert req.id not in all_req_ids_in_trips
        assert req.status == CollectionRequestStatus.PENDING

    res = create_trip(testapp, [req.id for req in requests])

    assert successful(res)

    all_req_ids_in_trips = [collection.id for trip in Trip.query.all() for collection in trip.collections]
    for req in requests:
        assert req.id in all_req_ids_in_trips
        assert req.status == CollectionRequestStatus.ASSIGNED


@pytest.fixture
def trip(requests, db):
    trip = Trip()
    trip.collections = requests
    db.session.add(trip)
    db.session.commit()
    return trip


def test_delete_trip(testapp, trip):
    assert trip is not None

    res = testapp.post(f'/api/admin/delete_trip', json={'id': trip.id})

    assert successful(res)
    # Trip must be deleted
    assert Trip.query.get(trip.id) is None

    # All the requests in the trip must still exist and now be pending
    for req in trip.collections:
        assert req.status == CollectionRequestStatus.PENDING


@pytest.fixture
def driver(db):
    driver = Employee(name=''.join(random.choices(string.ascii_letters)),
                      username=''.join(random.choices(string.ascii_letters)), password=bcrypt.hashpw(b"",bcrypt.gensalt()),
                      phone="0562316555",
                      role=EmployeeRole.DRIVER)
    db.session.add(driver)
    db.session.commit()
    return driver


def test_schedule_trip(testapp, trip, driver):
    resp = testapp.post(f'/api/admin/trip/{trip.id}/schedule', json={
        "driverId": driver.id,
        "timestamp": datetime.datetime.utcnow().timestamp() * 1000
    })
    assert successful(resp)

    for req in trip.collections:
        assert req.status == CollectionRequestStatus.SCHEDULED
