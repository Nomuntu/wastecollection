import re

from app.model import Employee, format_phone_number
from tests.conftest import successful


def test_add_driver(testapp):
    resp = testapp.post('/admin/add_driver', json={"name": "Driver Smith", "username": "driver", "phone": "0563215555"})
    assert successful(resp)
    retrieved = Employee.query.filter(Employee.username == "driver").first()
    assert retrieved is not None
    assert retrieved.phone == format_phone_number("0563215555")


def test_set_password(testapp):
    resp = testapp.post('/admin/add_driver', json={"name": "Driver Owen", "username": "driver2", "phone": "0563215555"})
    token_link = re.search(r'<a href="(.*)">', resp.data.decode("utf-8")).group(1)
    resp = testapp.post(token_link, json={"new_password": "hunter2"})
    assert successful(resp)

    resp = testapp.post('/login', json={"username": "driver2", "password": "hunter2", "phone": "0563215555"})
    assert successful(resp)
    assert b"/driver" in resp.data
