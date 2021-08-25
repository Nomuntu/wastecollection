# The Untum Waste Collection App

## Quick start
### Step 1: Set up a Google Cloud Platform account
Go to https://developers.google.com/maps/documentation/directions/cloud-setup
and follow through the steps. You **only** need `Directions API`.

After enabling the API, go to [API list](https://console.cloud.google.com/project/_/google/maps-apis/api-list),
on the left hand side click `Credentials`. You can copy the `Key` field of the
Directions API and save it somewhere for later.

### Step 2: Set up a Twilio account
Go to https://www.twilio.com/docs/sms/quickstart/python and follow the instructions
**up to** and including the section `Get a phone number`. You should
now have an `Account SID`, `Auth Token` and a phone number. Copy these
down somewhere for later

### Step 3: Deployment setup

The following steps are Heroku specific. If you wish to use a platform other than Heroku, please follow the
instructions in *Manual deployment* below.

**Heroku Caveat**: Each time you make a new deployment to Heroku (or restart Heroku's *dyno*), you will lose
the photos uploaded to the app. All other data will remain intact. This should not be a concern unless you are planning
on modifying the code (which would require redeployment).

If you wish to have the photos persist across deployments, you should use a server host with persistent file storage.

#### Heroku
Go to https://www.heroku.com/ and register an account.

Create a new app, give it a name.

Go to `Settings`, under `Config Vars` section click `Reveal Config Vars`.

Add the config vars. The name (`KEY`) and content (`VALUE`) are **CASE SENSITIVE**.
- `FLASK_SECRET`: a **long, random** string for security. You do not need to
remember this so don't set it to anything memorable
- `GCP_API_KEY`: Goolge Maps Direction API `Key` from Google Cloud Platform console you have copied
from Step 1
- `TWILIO_ACCOUNT_SID`: Twilio `Account SID` from Step 2
- `TWILIO_AUTH_TOKEN`: Twilio `Auth Token` from Step 2
- `TWILIO_PHONE`: Twilio phone number from Step 2
- `ADMIN_NAME`: Name of the administrator
- `ADMIN_PHONE`: Phone number of the administrator
- `ADMIN_INITIAL_PASSWORD`: The password the administrator will use to log in for the first time. They will have to
reset it on first login.

In the section `Buildpacks` below, click `Add Buildpack`.

Add `heroku/node.js` buildpack **and then** click `Add Buildpack` again and
add `heroku/python`. You should see `heroku/node.js` buildpack **above**
`heroku/python` in the `Buildpacks` section.

Add the `Heroku Postgres` add-on by going to https://elements.heroku.com/addons/heroku-postgresql.
Click `Install Heroku Postgres` then enter the name of the app you have just created,
click `Submit Order Form`.

Go to `Deploy` tab on the navbar. Follow the instruction under
`Deploy using Heroku Git`.

### Step 4: Post deployment
On the top right of the Heroku dashboard, you can click `Open app` to visit the newly deployed app. Append `/admin`
to the URL to visit the admin login page and log in with the username `admin` and the initial password you just set
in the previous step. You will be asked to reset the password and then log in again with the new password.

You can add drivers by visiting `/admin/add_driver`. They will receive a password reset link through SMS after you
fill in their details, so that they can set their own passwords.

You and the drivers can log out at any time by visiting `/logout`.

You and the drivers can also request a password reset link to be sent via SMS by visiting `/request_reset/{username}`,
where `{username}` is the username of the account.

#### Custom domains (optional)
If you want to host the app under your own domain name, go to `Settings` tab in your Heroku dashboard, and follow
the instructions under `Domain` section: [Configuring DNS](https://devcenter.heroku.com/articles/custom-domains).

## Configurations
Parameters the app uses can seen in `app/config.py`. The comment above each
parameter explains what they are.

Some of the parameters are taken from the environment variables by default. These parameters
should be kept secret. Where you may set the environment variables depends on the deployment platform you
use.

Instead of using environment variables, you may put the parameters directly in
`app/config.py` if it's on the deployment server and the content will not be
uploaded elsewhere.

The environment variable `FLASK_SECRET` **has to be set** to a long random string
for security.

### Third-party services
External services which **have to be configured** before deployment are:

* [Nominatim](https://operations.osmfoundation.org/policies/nominatim/)
* [Google Maps Platform](https://developers.google.com/maps/documentation/directions/cloud-setup)
* [Twilio](https://www.twilio.com/docs/sms/quickstart/python)

The usage policies of all of the above have to be reviewed before deployment.

Google Maps Platform and Twilio are paid services (though Google Maps Platform
has a generous $200 free monthly credit).

Nominatim is free to use but its [usage
policy](https://operations.osmfoundation.org/policies/nominatim/) must be
respected (most notably no more than 1 request per second can be made).

## Manual deployment
-   Prerequisites:
    ```
    Python 3.8
    pip
    npm
    postgresql
    ```

-   The environment variables required are the same as the ones mentioned in
    *Quick Start*
    

-   The connection to a Postgres database is specified by `DATABASE_URL`,
which is taken as an environment variable by default but it can be
specified directly in `app/app_config.py` (**not** `app/config.py`).
  
    The value for `DATABASE_URL` should be in the format:
    `postgresql://{user}:{password}@{host}:{port}/{database_name}`.


-   Install Node.js dependencies and run build.
    ```
    npm install
    npm run build
    ```

-   Install Python dependencies.
    ```
    pip3 install -r requirements.txt
    ```

-   Finally, start the server:
    ```
    gunicorn --worker-class eventlet -w 1 app.index:app --log-file -
    ```

## Continuous Integration & Continuous Deployment

`.gitlab-ci.yml` is included and can be used if CI/CD is desired.

## Branding configurations

Details of the waste entry form, waste management site location, photo
rescaling and the timezone can be configured in `app/config.py`.

The app's favicon is currently set to `app/static/img/logo.png`. It can be
configured by changing the `app/static/img/logo.png` file and/or editing
`app/templates/utils/base.html` to point to a different file.

The waste management provider's name can be configured by changing both of:
* `WASTE_MANAGEMENT_PROVIDER_NAME` in `app/config.py` (for SMS notifications)
* `<title>` in `app/templates/utils/base.html`

