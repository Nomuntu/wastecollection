import os

# Options for entering waste amounts (in kg)
BAG_SIZES = [25, 50, 1000, Bale]
MATERIAL_TYPES = [
    'Cardboard',
    'Paper',
    'Clear plastic',
    'Green plastic',
    'Aluminium'
]

# GPS Coordinates of the HQ site
HQ_COORDS = (-25.73, 31.87)

# Width to which photos are rescaled after uploading (in pixels)
PHOTO_WIDTH = 1024

# Timezone in which the dates are displayed
# A full list can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
# under TZ database name
TIMEZONE = 'Africa/Johannesburg'

# SMS verification code configuration
SMS_VERIFICATION_CODE_LENGTH = 6
SMS_EXPIRY_MINS = 5

# Google Cloud Platform API Key (for the Google Maps Directions API)
# See https://developers.google.com/maps/documentation/directions/cloud-setup
GCP_API_KEY = os.getenv('GCP_API_KEY')

# See https://www.twilio.com/docs/sms/quickstart/python
# for more details about Twilio
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE = os.getenv('TWILIO_PHONE')

# Company name to be displayed in SMS notifications
WASTE_MANAGEMENT_PROVIDER_NAME = 'Untum (Pty) Ltd'

# Name of the administrator
ADMIN_NAME = os.environ['ADMIN_NAME']
# Phone number of the administrator
ADMIN_PHONE = os.environ['ADMIN_PHONE']
# Default password of the "admin" account
ADMIN_INITIAL_PASSWORD = os.environ['ADMIN_INITIAL_PASSWORD']
