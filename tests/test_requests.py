import base64
import json
import os
from decimal import Decimal
from io import BytesIO

import pytest

from app.model import CollectionRequest, CollectionRequestStatus
from app.photo_processing import STORAGE_PATH
from tests.conftest import successful


@pytest.fixture
def request_info():
    waste_entry_one = {'bag_size': 25, 'material': 'aluminium', 'num_bags': 5}
    waste_entry_two = {'bag_size': 50, 'material': 'plastic', 'num_bags': 2}

    return {
        'loc': {'lat': -25.7277771, 'lon': 31.8680944},
        'waste': [waste_entry_one, waste_entry_two]
    }


def test_request_submission(testapp, request_info):
    with testapp.session_transaction() as sess:
        sess['name'] = 'jess'
        sess['phone'] = '0812222222'

    response = testapp.post('/api/submit_request',
                            data={'info': json.dumps(request_info)})
    print(f'response: {response}')

    res = CollectionRequest.query.filter_by(collector_name='jess')

    assert res.count() == 1
    row = res.first()
    assert row.collector_name == 'jess'
    assert row.collector_phone == '+27812222222'

    assert row.address is not None
    assert row.address['village'] == 'Theresapark Village'
    assert row.status == CollectionRequestStatus.PENDING

    waste_entries = row.waste_entries
    assert len(waste_entries) == 2
    assert waste_entries[0].bag_size == request_info['waste'][0]['bag_size']
    assert waste_entries[1].bag_size == request_info['waste'][1]['bag_size']


def test_manual_request_submission(testapp, request_info):
    request_info['name'] = 'jess'
    request_info['phone'] = '0812222222'

    response = testapp.post('/api/admin/submit_manual_request',
                            data={'info': json.dumps(request_info)})
    print(f'response: {response}')

    res = CollectionRequest.query.filter_by(collector_name='jess')

    assert res.count() == 1
    row = res.first()
    assert row.collector_name == 'jess'
    assert row.collector_phone == '+27812222222'

    assert row.address is not None
    assert row.address['village'] == 'Theresapark Village'
    assert row.status == CollectionRequestStatus.PENDING

    waste_entries = row.waste_entries
    assert len(waste_entries) == 2
    assert waste_entries[0].bag_size == request_info['waste'][0]['bag_size']
    assert waste_entries[1].bag_size == request_info['waste'][1]['bag_size']


def test_request_deletion(testapp, request_info, db):
    with testapp.session_transaction() as sess:
        sess['name'] = 'not jess'
        sess['phone'] = '0812222222'

    response = testapp.post('/api/submit_request',
                            data={'info': json.dumps(request_info),
                                  'photo': (BytesIO(base64.b64decode('R0lGODlhAQABAIAAAP///wAAACwAAAAAAQABAAACAkQBADs=')), "photo")})
    assert successful(response)

    req = CollectionRequest.query.filter_by(collector_name='not jess').first()
    photo_path = f'{STORAGE_PATH}/{req.photo_id}'
    assert os.path.exists(photo_path)
    response = testapp.post('/api/admin/delete_request', json={'id': req.id})
    assert successful(response)
    assert not os.path.exists(photo_path)


@pytest.fixture
def request_model(db):
    req = CollectionRequest(collector_name='jess', collector_phone='0812222222', location_lat=Decimal('1.22'),
                            location_lon=Decimal('2.22'), waste_entries=[])
    db.session.add(req)
    db.session.commit()
    return req


def test_mark_as_complete(testapp, request_model):
    assert request_model.status == CollectionRequestStatus.PENDING
    assert b'Mark as complete' in testapp.get(f'/admin/view_request/{request_model.id}').data

    testapp.get(f'/api/mark_as_complete/{request_model.id}')
    assert request_model.status == CollectionRequestStatus.COMPLETED
    assert b'Collection has been completed' in testapp.get(f'/admin/view_request/{request_model.id}').data
