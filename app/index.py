import datetime
import json
import os

import bcrypt

from app import config
from app.app_config import ProductionConfig
from app.blueprint import create_app

app = create_app(ProductionConfig())

with app.app_context():
    from app.model import *

    admin = Employee.query.filter(Employee.username == "admin").first()
    if admin is None:
        admin = Employee(name=config.ADMIN_NAME,
                         username="admin",
                         password=bcrypt.hashpw(config.ADMIN_INITIAL_PASSWORD.encode("utf-8"), bcrypt.gensalt()),
                         phone=config.ADMIN_PHONE,
                         role=EmployeeRole.ADMIN)
        db.session.add(admin)
    else:
        admin.name = config.ADMIN_NAME
        admin.phone = config.ADMIN_PHONE
    db.session.commit()
