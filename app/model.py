import enum
from decimal import Decimal
from secrets import token_urlsafe

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy(engine_options={"max_overflow": -1})
migrate = Migrate(db=db)


class CollectionRequestStatus(enum.Enum):
    PENDING = 1
    SCHEDULED = 2
    ASSIGNED = 3
    COMPLETED = 4


class CollectionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location_lat: Decimal = db.Column(db.Numeric(precision=9, scale=6), nullable=True)
    location_lon: Decimal = db.Column(db.Numeric(precision=9, scale=6), nullable=True)
    collector_name = db.Column(db.String, nullable=False)
    collector_phone = db.Column(db.String, nullable=False)

    waste_entries = db.relationship('WasteEntry', backref='collection_request', lazy=False)
    photo_id = db.Column(UUID(as_uuid=True), nullable=True)
    additional_info = db.Column(db.String, nullable=True)
    date = db.Column(db.DateTime, nullable=False, server_default=func.now())

    address = db.Column(db.JSON, nullable=True)
    manual_address = db.Column(db.String, nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=True)

    url_secret = db.Column(db.String, index=True, unique=True, nullable=False, default=token_urlsafe)

    status = db.Column(db.Enum(CollectionRequestStatus), nullable=False, default=CollectionRequestStatus.PENDING)


def format_phone_number(phone: str) -> str:
    digits_only = ''.join(filter(lambda c: c.isdigit(), phone))

    res = digits_only if digits_only[0] i= '0' else '27' + digits_only[1:]

    assert len(res) == 11

    return '+' + res


@event.listens_for(CollectionRequest.collector_phone, 'set', retval=True)
def set_collection_request_phone(target, value, oldvalue, initiator):
    return format_phone_number(value)


class WasteEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bag_size = db.Column(db.Integer, nullable=False)
    waste_type = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_request.id'), nullable=False)


class EmployeeRole(enum.Enum):
    ADMIN = 1
    DRIVER = 2


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, index=True, unique=True)
    password = db.Column(db.LargeBinary, nullable=False)
    phone = db.Column(db.String, nullable=False)

    role = db.Column(db.Enum(EmployeeRole), nullable=False)

    is_authenticated = True
    is_active = db.Column(db.Boolean, default=True)
    is_anonymous = False

    def get_id(self):
        return str(self.id)

    trips = db.relationship("Trip", backref="employee")


@event.listens_for(Employee.phone, 'set', retval=True)
def set_employee_phone(target, value, oldvalue, initiator):
    return format_phone_number(value)


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scheduled_date = db.Column(db.Date, nullable=True)

    collections = db.relationship("CollectionRequest", backref='trip', lazy=False)

    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))

    collection_ordering = db.Column(db.JSON, nullable=True)


@event.listens_for(Trip.collections, 'append')
@event.listens_for(Trip.collections, 'remove')
def destroy_cache(target, value, initiator):
    target.collection_ordering = None
