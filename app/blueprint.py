import datetime
import json
import secrets
from json import JSONEncoder
from flask_socketio import SocketIO
from typing import *
from urllib.parse import urlparse, urljoin

import bcrypt
from flask import Blueprint, redirect, render_template, url_for, abort, session, current_app, flash
from flask import Flask, request, jsonify
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from flask_session import Session
from pytz import timezone

import app.config as config
from app.app_config import AppConfig
from app.model import *
from app.services.optimize_waypoints import optimize_waypoints, trip_maps_url
from app.photo_processing import save_photo, photo_url
from app.services.reverse_geocode import reverse_geocode
from app.token import verify_token, generate_token

from app.services.sms_provider import send_sms, generate_sms_code, initialise_sms_client

blueprint = Blueprint('app', __name__)
login_manager = LoginManager()
login_manager.login_view = "app.employee_login"
sess = Session()
socketio = SocketIO()

TZ_INFO = timezone(config.TIMEZONE)


def create_app(config_object: AppConfig) -> Flask:
    app = Flask(__name__)

    app.url_map.strict_slashes = False
    app.config.from_object(config_object)

    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app)
    sess.init_app(app)
    socketio.init_app(app)

    app.session_interface.db.create_all()
    with app.app_context():
        db.create_all()

    app.register_error_handler(404, page_not_found)

    app.register_blueprint(blueprint)
    initialise_sms_client(app)

    return app


def page_not_found(e):
    return render_template('page_not_found.html'), 404


@blueprint.before_request
def verify_role():
    if not current_user.is_authenticated:
        # If the visitor isn't logged in they'll be bounced by login_required on the routes themselves
        return

    admin_prefix = ["/admin", "/api/admin"]

    admin_only = any(map(request.path.startswith, admin_prefix))
    if admin_only and current_user.role != EmployeeRole.ADMIN:
        return f"Your role ({current_user.role}) is unauthorised to visit this page", 403


def notify_collectors(trip_id, alert_collector_message):
    trip = Trip.query.get(trip_id)

    for collection in trip.collections:
        cname = collection.collector_name
        message = alert_collector_message(cname)
        send_sms(collection.collector_phone, message)


@event.listens_for(CollectionRequest, 'after_insert')
def notify_admin(mapper, connection, target: CollectionRequest):
    req = json.dumps(RequestInfo(target), cls=RequestInfoEncoder)
    pin = json.dumps(extract_pin(target), cls=RequestInfoEncoder)
    socketio.emit('data', {'req': req, 'pin': pin})


class RequestInfoEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, RequestInfo):
            return {
                'id': o.id,
                'name': o.name,
                'phone_num': o.phone_num,
                'address': o.address,
                'manual_address': o.address,
                'loc': {
                    'lat': o.location[0],
                    'lon': o.location[1]
                },
                'date': o.date,
                'timestamp': o.timestamp,
                'image_path': o.image_path,
                'waste_entries': o.waste_entries,
                'additional_info': o.additional_info,
                'status': o.status.name,
                'maps_url': o.maps_url()
            }
        elif isinstance(o, Decimal):
            # o.location is a tuple of Decimal but it doesn't have a default encoder
            return float(o)
        return JSONEncoder.default(self, o)


@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))


@blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('app.employee_login'))


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    if session.get('verified'):  # It could be None, so we write is true
        return redirect('/new_request')

    def verification_message(name, code):
        return f'Hi, {name}! This is your verification code for {config.WASTE_MANAGEMENT_PROVIDER_NAME}: {code}. It is valid for 5 minutes'

    if request.method == 'POST':
        session['name'] = request.json.get('name')
        session['phone'] = request.json.get('phone')
        sms_code = generate_sms_code()
        session['sms_code'] = sms_code
        session['expiry'] = datetime.datetime.now() + datetime.timedelta(minutes=config.SMS_EXPIRY_MINS)
        session['verified'] = False

        phone_formatted = format_phone_number(session.get('phone'))

        send_sms(phone_formatted, verification_message(session.get('name'), sms_code))
        return url_for('app.collector_verification')

    return render_template('picker/login.html')


@blueprint.route('/collector_verification', methods=['GET', 'POST'])
def collector_verification():
    if session.get('name') is None or session.get('phone') is None:
        return redirect('/')
    elif session.get('verified'):
        return redirect('/new_request')

    if request.method == 'POST':
        entered_code = request.json.get('smsCode')

        response = {}
        response['expired'] = datetime.datetime.now() > session.get('expiry')
        response['code_correct'] = entered_code == session.get('sms_code')

        if response.get('expired'):
            response['url'] = url_for('app.index')
        elif not response.get('code_correct'):
            response['url'] = url_for('app.collector_verification')
        else:
            session['verified'] = True
            response['url'] = url_for('app.new_request')

        return jsonify(response)
    else:
        return render_template('picker/sms_verify.html', phone_number=str(session.get('phone')))


@blueprint.route('/new_request')
def new_request():
    if not session.get('verified'):
        return redirect('/')

    return render_template('picker/new_request.html',
                           bag_sizes=config.BAG_SIZES,
                           material_types=config.MATERIAL_TYPES, photo_width=config.PHOTO_WIDTH)


@blueprint.route('/api/submit_request', methods=['POST'])
def submit_request():
    data = json.loads(request.form.get("info"))

    print(f"Collection request: {data}")
    print(f"With session data: {session}")

    photo = request.files.get("photo")
    photo_id = None
    if photo is not None:
        photo_id = save_photo(photo)

    location_dict = data.get('loc')

    lon = None
    lat = None
    address = None
    manual_address = None

    if location_dict is not None and len(location_dict) != 0:
        address = reverse_geocode(location_dict['lat'], location_dict['lon'])
        lon = location_dict['lon']
        lat = location_dict['lat']
    else:
        manual_address = data.get('manual_loc')

    collection_request = CollectionRequest(location_lon=lon,
                                           location_lat=lat,
                                           collector_name=session['name'],
                                           collector_phone=session['phone'],
                                           address=address,
                                           manual_address=manual_address,
                                           photo_id=photo_id,
                                           additional_info=data.get('additional_info'),
                                           status=CollectionRequestStatus.PENDING)

    def extract_waste_entry(entry):
        bag_size = int(entry.get('bag_size'))
        waste_type = entry.get('material')
        quantity = int(entry.get('num_bags'))
        return WasteEntry(bag_size=bag_size, waste_type=waste_type, quantity=quantity)

    waste_entries = map(extract_waste_entry, data.get('waste'))

    collection_request.waste_entries.extend(waste_entries)

    db.session.add(collection_request)
    db.session.commit()

    return url_for('app.request_waiting', req_secret=collection_request.url_secret), 201


@blueprint.route('/api/admin/submit_manual_request', methods=['POST'])
def submit_manual_request():
    data = json.loads(request.form.get("info"))

    print(f"Manual collection request: {data}")

    photo = request.files.get("photo")
    photo_id = None
    if photo is not None:
        photo_id = save_photo(photo)

    location_dict = data.get('loc')

    address = reverse_geocode(location_dict['lat'], location_dict['lon'])

    collection_request = CollectionRequest(location_lon=location_dict['lon'],
                                           location_lat=location_dict['lat'],
                                           collector_name=data.get('name'),
                                           collector_phone=data.get('phone'),
                                           address=address,
                                           photo_id=photo_id,
                                           status=CollectionRequestStatus.PENDING)

    def extract_waste_entry(entry):
        bag_size = int(entry.get('bag_size'))
        waste_type = entry.get('material')
        quantity = int(entry.get('num_bags'))
        return WasteEntry(bag_size=bag_size, waste_type=waste_type, quantity=quantity)

    waste_entries = map(extract_waste_entry, data.get('waste'))

    collection_request.waste_entries.extend(waste_entries)

    db.session.add(collection_request)
    db.session.commit()

    return "", 201


@blueprint.route('/request_waiting/<string:req_secret>')
def request_waiting(req_secret):
    if not session.get('verified'):
        return redirect('/')

    req = CollectionRequest.query.filter(CollectionRequest.url_secret == req_secret).first_or_404()

    if format_phone_number(session.get('phone')) != req.collector_phone:
        return redirect('/')

    req_info = RequestInfo(req)
    if req_info.pending() or req_info.assigned():
        return render_template('picker/request_waiting.html', waste_entries=req_info.waste_entries)
    elif req_info.scheduled():
        return render_template('picker/pickup_confirmation.html',
                               pickup_date=req.trip.scheduled_date.strftime("%a %d %b %Y"),
                               maps_url=req_info.maps_url(), comments=None)


def address_pretty_print(address: Dict[str, str]) -> Optional[str]:
    if address is None:
        return None

    return ', '.join(
        [address[granularity]
         for granularity in ['suburb', 'village', 'city']
         if granularity in address])


def location_to_maps_url(latitude, longitude) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude}%2C{longitude}"


def date_pretty_print(date: datetime) -> str:
    return date.strftime("%a %d %b %Y %R")


class RequestInfo:
    def __init__(self, req: CollectionRequest):
        self.id = req.id
        self.name = req.collector_name
        self.phone_num = req.collector_phone
        self.address = address_pretty_print(req.address)
        self.manual_address = req.manual_address
        self.location = (req.location_lat, req.location_lon)
        self.date = date_pretty_print(req.date.astimezone(TZ_INFO))
        self.timestamp = req.date.timestamp()
        self.image_path = photo_url(req.photo_id) if req.photo_id else None
        self.waste_entries = [{'bag_size': entry.bag_size,
                               'material': entry.waste_type,
                               'num_bags': entry.quantity,
                               'total_weight': entry.bag_size * entry.quantity}
                              for entry in req.waste_entries]
        self.additional_info = req.additional_info
        self.status = req.status

    def pending(self):
        return self.status == CollectionRequestStatus.PENDING

    def assigned(self):
        return self.status == CollectionRequestStatus.ASSIGNED

    def scheduled(self):
        return self.status == CollectionRequestStatus.SCHEDULED

    def completed(self):
        return self.status == CollectionRequestStatus.COMPLETED

    def maps_url(self) -> str:
        return location_to_maps_url(self.location[0], self.location[1])


def extract_pin(req: CollectionRequest, msg: Optional[str] = None) -> Optional[Dict[str, object]]:
    if req.location_lat is None:
        return None
    return {'lat': req.location_lat,
            'lon': req.location_lon,
            'reqId': req.id,
            'msg': req.collector_name if msg is None else msg}


@blueprint.route('/login', methods=['GET', 'POST'])
def employee_login():
    def is_safe_url(next_url):
        host_url = urlparse(request.host_url)
        redirect_url = urlparse(urljoin(request.host_url, next_url))
        return host_url.scheme == redirect_url.scheme and host_url.netloc == redirect_url.netloc

    def goto_url():
        next_url = request.args.get('next')
        if not is_safe_url(next_url):
            return abort(400)

        if current_user.role == EmployeeRole.ADMIN:
            return next_url or url_for('app.admin')
        elif current_user.role == EmployeeRole.DRIVER:
            return next_url or url_for('app.driver')
        else:
            raise RuntimeError(f"Unknown employee role {current_user.role}")

    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(goto_url())
        else:
            return render_template('employee_login.html')
    else:
        username = request.json.get('username')
        password = request.json.get('password')
        if username is None or password is None:
            return "Empty credential", 400

        employee = Employee.query.filter(Employee.username == username).one_or_none()
        if employee is None:
            return "Unauthorised", 401
        if not bcrypt.checkpw(password.encode('utf-8'), employee.password):
            return "Unauthorised", 401

        login_user(employee)

        return goto_url(), 200


@blueprint.route('/admin')
@login_required
def admin():
    assert current_user.role == EmployeeRole.ADMIN
    if bcrypt.checkpw(config.ADMIN_INITIAL_PASSWORD.encode("utf-8"), current_user.password):
        # Admin used default password to log in
        token = generate_token(current_user.id, datetime.datetime.utcnow() + datetime.timedelta(days=3), current_app.secret_key)
        flash("Please reset your password")
        return redirect(url_for("app.reset_password", token=token))

    requests = CollectionRequest.query.all()
    ungrouped_data = [RequestInfo(req) for req in requests]

    grouped_data = {'pending': [], 'scheduled': [], 'completed': []}
    for req in ungrouped_data:
        if req.pending():
            grouped_data['pending'].append(req)
        elif req.scheduled():
            grouped_data['scheduled'].append(req)
        elif req.completed():
            grouped_data['completed'].append(req)

    # We need only display the pending pins
    pins = [extract_pin(req) for req in requests if
            req.status == CollectionRequestStatus.PENDING and req.location_lat is not None]

    trips = Trip.query.order_by(Trip.id.desc()).all()

    return render_template('admin/admin.html',
                           name=current_user.name,
                           data=grouped_data,
                           pins=pins,
                           trips=trips)


@blueprint.route('/view_request/<int:req_id>')
@login_required
def view_request_route(req_id):
    if current_user.role == EmployeeRole.ADMIN:
        return redirect(url_for('app.view_request_admin', req_id=req_id))
    elif current_user.role == EmployeeRole.DRIVER:
        return redirect(url_for('app.view_request_driver', req_id=req_id))


@blueprint.route('/admin/view_request/<int:req_id>')
@login_required
def view_request_admin(req_id) -> str:
    return view_request(req_id)


@blueprint.route('/driver/view_request/<int:req_id>')
@login_required
def view_request_driver(req_id) -> str:
    return view_request(req_id)


def view_request(req_id) -> str:
    req = CollectionRequest.query.get_or_404(req_id)

    pin = extract_pin(req)
    if pin is not None:
        pin['zoom'] = 12

    return render_template('/view_request.html',
                           req=RequestInfo(req),
                           loc=pin,
                           pins=[pin],
                           bag_sizes=config.BAG_SIZES,
                           material_types=config.MATERIAL_TYPES)


@blueprint.route('/api/mark_as_complete/<int:req_id>')
@login_required
def mark_as_complete(req_id):
    req = CollectionRequest.query.get_or_404(req_id)
    req.status = CollectionRequestStatus.COMPLETED
    db.session.commit()
    return '', 204


@blueprint.route('/api/admin/update_request/', methods=['POST'])
def update_request():
    req = request.json
    initial_req = CollectionRequest.query.get_or_404(req['id'])

    for (k, v) in req.items():
        if k == 'loc':
            address = reverse_geocode(req['loc']['lat'], req['loc']['lon'])
            initial_req.address = address
            initial_req.location_lat = req['loc']['lat']
            initial_req.location_lon = req['loc']['lon']
        elif k == 'name':
            initial_req.collector_name = req['name']
        elif k == 'phone':
            initial_req.collector_phone = req['phone']
        elif k == 'waste_entries':
            def extract_waste_entry(entry):
                bag_size = entry.get('bag_size')
                waste_type = entry.get('material')
                quantity = entry.get('num_bags')
                return WasteEntry(bag_size=bag_size, waste_type=waste_type, quantity=quantity)

            waste_entries = map(extract_waste_entry, req['waste_entries'])
            for waste_entry in initial_req.waste_entries:
                db.session.delete(waste_entry)

            initial_req.waste_entries.extend(waste_entries)

    db.session.commit()

    return '', 200


@blueprint.route('/api/admin/delete_request/', methods=['POST'])
def delete_request():
    req = request.json
    req = CollectionRequest.query.get_or_404(req['id'])

    for waste_entry in req.waste_entries:
        db.session.delete(waste_entry)

    db.session.delete(req)
    db.session.commit()

    return '', 200


@blueprint.route('/admin/manual_request')
def admin_manual_request() -> str:
    return render_template('admin/manual_request.html',
                           bag_sizes=config.BAG_SIZES,
                           material_types=config.MATERIAL_TYPES)


@blueprint.route('/api/admin/add_to_trip', methods=['POST'])
@login_required
def add_to_trip():
    req_ids = request.json['reqIds']
    trip_id = request.json['tripId']

    if req_ids is None or len(req_ids) == 0:
        return '', 400

    print(f'Req ids: {req_ids}')

    collection_requests = CollectionRequest.query \
        .filter(CollectionRequest.id.in_(req_ids)) \
        .all()

    if trip_id == 'new_trip':
        trip = Trip(collections=collection_requests)
        db.session.add(trip)

        print(f'Created a new trip: id={trip.id}, requests={collection_requests}')
    else:
        trip = Trip.query.get_or_404(int(trip_id))
        trip.collections += collection_requests

        print(f'Added the following requests to an existing trip with id {trip_id}: {collection_requests}')

    for req in collection_requests:
        req.status = CollectionRequestStatus.ASSIGNED

    db.session.commit()

    return '', 204


@blueprint.route('/api/admin/delete_trip/', methods=['POST'])
@login_required
def delete_trip():
    trip_id = request.json['id']
    trip = Trip.query.get_or_404(trip_id)

    collection_requests = trip.collections

    print(f'Deleting trips with collections: {collection_requests}')

    for req in collection_requests:
        req.status = CollectionRequestStatus.PENDING

    db.session.delete(trip)
    db.session.commit()

    return '', 200


@blueprint.route('/api/admin/update_trip/', methods=['POST'])
def update_trip():
    trip = request.json
    initial_trip = Trip.query.get_or_404(trip['id'])

    initial_trip.employee_id = trip['driverId']
    initial_trip.scheduled_date = datetime.date.fromtimestamp(trip['timestamp'] / 1000)

    for req in initial_trip.collections:
        if str(req.id) in trip['removed_requests']:
            req.status = CollectionRequestStatus.PENDING
            initial_trip.collections.remove(req)

    db.session.commit()

    return '', 200


# Triggered when a new request is added to a Trip
@event.listens_for(Trip.collections, 'append')
def append_collection(target: Trip, value: CollectionRequest, initiator):
    if target.scheduled_date is None:
        return

    collection_driver = Employee.query.get(target.employee_id)

    def alert_collector_message(collector_name):
        if collection_driver is None:
            return f'Hi {collector_name}! Our driver will collect your waste on {target.scheduled_date}'
        else:
            return f'Hi {collector_name}! {collection_driver.name} will collect your waste on {target.scheduled_date}'

    message = alert_collector_message(value.collector_name)
    send_sms(value.collector_phone, message)


# Triggered when a request is removed from a Trip
@event.listens_for(Trip.collections, 'remove')
def removed_collection(target: Trip, value, initiator):
    if target.scheduled_date is None:
        return

    def alert_collector_message(collector_name):
        return f'Hi {collector_name}. We are sorry that your collection on {target.scheduled_date} has been ' \
               f'cancelled. We will let you know shortly when your new collection date will be.'

    message = alert_collector_message(value.collector_name)
    send_sms(value.collector_phone, message)


# Triggered when a trip is updated with a new date
@event.listens_for(Trip.scheduled_date, 'set')
def updated_trip(target: Trip, value, old_value, initiator):
    collection_driver = Employee.query.get(target.employee_id)

    def alert_collector_message(collector_name):
        if collection_driver is None:
            return f'Hi {collector_name}! Our driver will collect your waste on {value}'
        else:
            return f'Hi {collector_name}! {collection_driver.name} will collect your waste on {value}'

    if value != old_value:
        notify_collectors(target.id, alert_collector_message)


# Triggered when a trip is cancelled
@event.listens_for(Trip, 'after_delete')
def cancelled_trip(mapper, connection, target: Trip):
    def alert_collector_message(collector_name):
        return f'Hi {collector_name}. We are sorry that your collection on {target.scheduled_date} has been ' \
               f'cancelled. We will let you know shortly when your new collection date will be.'

    notify_collectors(target.id, alert_collector_message)


@blueprint.route('/driver')
@login_required
def driver() -> str:
    trips = Trip.query.filter(current_user.id == Trip.employee_id)
    return render_template('driver/driver.html', name=current_user.name, trips=trips)


@blueprint.route('/driver/trip/<int:trip_id>')
@login_required
def trip_driver(trip_id: int) -> str:
    data, pins = get_trip_data(trip_id)
    return render_template('driver/trip.html', trip=data, pins=pins)


@blueprint.route('/admin/trip/<int:trip_id>')
@login_required
def trip_admin(trip_id: int) -> str:
    data, pins = get_trip_data(trip_id)

    drivers = Employee.query.filter(Employee.role == EmployeeRole.DRIVER).all()

    data['driver_list'] = [
        {'name': driver.name, 'id': driver.id}
        for driver in drivers
    ]

    return render_template('admin/trip.html', trip=data, pins=pins)


@blueprint.route('/admin/add_driver', methods=["GET", "POST"])
@login_required
def add_driver():
    if request.method == "GET":
        return render_template("admin/add_driver.html")
    else:
        name = request.json["name"]
        username = request.json["username"]
        phone = request.json["phone"]
        if Employee.query.filter(Employee.username == username).first() is not None:
            return "Username taken", 409
        # password won't be a valid bcrypt bytestring. Secure random bytes just as placeholder
        # to be overwritten on later reset.
        drvr = Employee(name=name, username=username, phone=phone, password=secrets.token_bytes(), role=EmployeeRole.DRIVER)

        db.session.add(drvr)
        db.session.commit()
        token = generate_token(drvr.id, datetime.datetime.utcnow() + datetime.timedelta(days=3), current_app.secret_key)
        password_link = url_for('app.reset_password', token=token, _external=True)
        current_app.logger.info(
            f"Created driver id: {drvr.id}, name: {drvr.name}, reset link: {password_link}")
        return render_template("admin/add_driver_success.html", name=name, username=username,
                               password_link=password_link)


@blueprint.route('/request_reset/<string:username>')
def request_reset(username):
    employee = Employee.query.filter(Employee.username == username).first_or_404()
    token = generate_token(employee.id, datetime.datetime.utcnow() + datetime.timedelta(days=3), current_app.secret_key)
    reset_link = url_for('app.reset_password', token=token, _external=True)
    current_app.logger.info(
        f"Employee id: {employee.id}, name: {employee.name}, reset link: {reset_link}")
    send_sms(employee.phone, f"Reset your {config.WASTE_MANAGEMENT_PROVIDER_NAME} password here: {reset_link}")
    return "", 200


@blueprint.route('/reset_password/<string:token>', methods=["GET", "POST"])
def reset_password(token):
    try:
        employee_id = verify_token(token, current_app.secret_key)
    except Exception as e:
        current_app.logger.error(e)
        return "Invalid auth token", 403

    logout_user()
    employee = Employee.query.get_or_404(employee_id)
    if request.method == "GET":
        return render_template("reset_password.html")
    else:
        new_password = request.json["new_password"]
        employee.password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        db.session.commit()
        flash("Reset successful")
        return url_for("app.employee_login"), 200


def get_trip_data(trip_id):
    trp: Trip = Trip.query.get_or_404(trip_id)

    collections: List[CollectionRequest] = trp.collections

    villages = [
        collection.address['village']
        for collection in collections
        if collection.address is not None and 'village' in collection.address
    ]

    location_name = villages[0] if len(villages) > 0 else 'Unknown'

    data = {
        'id': trip_id,
        'location': location_name,
        'number': len(collections),
        'employee': trp.employee.name if trp.employee else 'Unassigned',
        'date': trp.scheduled_date
    }

    if len(collections) == 0:
        data.update({
            'requests': [],
            'maps_url': None,
            'optimization_successful': False
        })

        return data, []

    optimization_ids = trp.collection_ordering

    optimization_successful = True

    # if no cached ordering
    if optimization_ids is None:
        optimization_successful, requests_optimized, err_msg = optimize_waypoints(collections)

        if optimization_successful:
            # cache the calculated ordering
            optimization_ids = [request.id for request in requests_optimized]
            trp.collection_ordering = optimization_ids

            db.session.commit()

        elif err_msg is not None:
            data['err_msg'] = err_msg

    else:
        requests_optimized = [next(filter(lambda collection: collection.id == id, collections))
                              for id in optimization_ids]

    data.update({
        'requests': [RequestInfo(req) for req in requests_optimized],
        'maps_url': trip_maps_url(requests_optimized),
        'optimization_successful': optimization_successful
    })

    pins = [extract_pin(collection) for collection in collections]

    return data, pins


@blueprint.route('/api/admin/trip/<int:trip_id>/schedule', methods=['POST'])
@login_required
def schedule_trip(trip_id):
    driver_id = request.json.get('driverId')
    scheduled_timestamp = request.json.get('timestamp')

    print(f'Driver id: {driver_id}. Scheduled date: {scheduled_timestamp}')

    trip = Trip.query.get(trip_id)

    trip.employee_id = driver_id
    trip.scheduled_date = datetime.date.fromtimestamp(scheduled_timestamp / 1000)
    for req in trip.collections:
        req.status = CollectionRequestStatus.SCHEDULED

    db.session.commit()
    return "", 204
