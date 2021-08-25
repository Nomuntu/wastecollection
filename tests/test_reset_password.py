from datetime import datetime, timedelta

import bcrypt

from app.model import Employee, EmployeeRole
from app.token import generate_token
from tests.conftest import TestConfig, successful


def test_bad_token(testapp):
    resp = testapp.get('/reset_password/a')
    assert not successful(resp)

    resp = testapp.get('/reset_password/')
    assert not successful(resp)


def test_reset(testapp, db):
    admin = Employee(name="Admin",
                     username="adminadmin",
                     password=bcrypt.hashpw(b"admin", bcrypt.gensalt()),
                     phone="0562316555",
                     role=EmployeeRole.ADMIN)
    db.session.add(admin)
    db.session.commit()

    token = generate_token(admin.id, datetime.utcnow() + timedelta(days=3), TestConfig.SECRET_KEY)

    resp = testapp.get(f'/reset_password/{token}')
    assert successful(resp)

    resp = testapp.post(f'/reset_password/{token}',
                        json={'new_password': "newpassword"})
    assert successful(resp)
    new_db_password = Employee.query.get(admin.id).password
    assert bcrypt.checkpw(b"newpassword", new_db_password)
