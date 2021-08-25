from flask import current_app

import app.config as config
from twilio.rest import Client
from random import randrange

client = None


def initialise_sms_client(app):
    global client
    if app.config['ENV'] == "production":

        if config.TWILIO_ACCOUNT_SID is None or config.TWILIO_AUTH_TOKEN is None or config.TWILIO_PHONE is None:
            raise Exception('Environment variables TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_PHONE'
                            ' have to be set in production')

        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def send_sms(phone: str, message: str):
    if current_app.config["ENV"] == "production":
        if client is None:
            raise Exception('SMS provider client not set')

        client.messages.create(
           body=message,
           from_=config.TWILIO_PHONE,
           to=phone
        )

        print(f'Sent to {phone}:\n{message}')


def generate_sms_code() -> str:
    code = ""
    for _ in range(config.SMS_VERIFICATION_CODE_LENGTH):
        code += str(randrange(0, 10))

    return code
