import json
import os
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth_oauthlib.flow
from flask import Flask, request, redirect, session, url_for, render_template, flash
from flask.json import jsonify
from requests_oauthlib import OAuth2Session

# Local Imports
from utils import credentials_to_dict
from forms import FBForm, CreateAndroidAppForm, AndroidAppForm


app = Flask(__name__)

with open('client_secret.json') as json_file:
    client_secret = json.load(json_file)

SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/cloud-platform.read-only',
    'https://www.googleapis.com/auth/cloudplatformprojects',
    'https://www.googleapis.com/auth/firebase',
    'https://www.googleapis.com/auth/firebase.readonly',
]

API_SERVICE_NAME_RESOURCEMANAGAER = 'cloudresourcemanager'
API_VERSION_RESOURCE_MANAGER = 'v1'


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/gcpProjs')
def get_gcp_projects():
    """Get you GCP projects"""
    session['redirect_to'] = "get_gcp_projects"
    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    service = googleapiclient.discovery.build(
        API_SERVICE_NAME_RESOURCEMANAGAER, API_VERSION_RESOURCE_MANAGER, credentials=credentials)

    session['credentials'] = credentials_to_dict(credentials)
    _request = service.projects().list(filter=None)
    response = _request.execute()
    return response


@app.route('/fbProjs')
def get_firebase_projects():
    """Get all FireBase projects """

    session['redirect_to'] = "get_firebase_projects"
    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    google.oauth2.credentials.Credentials(
        **session['credentials'])
    fb = OAuth2Session(client_id=client_secret['web']['client_id'], token=session['oauth_token'])

    # You need to enable Firebase Management API for this to work.
    # Visit : https://console.developers.google.com/apis/api/firebase.googleapis.com/overview?project=project_id
    resp = fb.get('https://firebase.googleapis.com/v1beta1/projects')

    return jsonify(resp.json())


@app.route('/androidApps', methods=['POST'])
def get_android_apps():
    """Get all Android apps """
    print(request.form)
    if request.method == 'POST':
        fb_proj = request.form['fb_proj']

    session['redirect_to'] = "get_android_apps"
    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    google.oauth2.credentials.Credentials(
        **session['credentials'])
    fb = OAuth2Session(client_id=client_secret['web']['client_id'], token=session['oauth_token'])

    print(fb_proj)
    resp = fb.get(f'https://firebase.googleapis.com/v1beta1/projects/{fb_proj}/androidApps')

    return jsonify(resp.json())


@app.route('/getApps', methods=["GET", "POST"])
def get_app_page():
    session['redirect_to'] = "get_app_page"
    form = AndroidAppForm()
    if request.method == 'GET':
        return render_template('getApp.html', form=form)
    elif request.method == 'POST':
        fb_proj = request.form['fb_proj']
        if 'credentials' not in session:
            return redirect('authorize')

        # Load credentials from the session.
        google.oauth2.credentials.Credentials(
            **session['credentials'])
        fb = OAuth2Session(client_id=client_secret['web']['client_id'], token=session['oauth_token'])
        resp = fb.get(f'https://firebase.googleapis.com/v1beta1/projects/{fb_proj}/androidApps')

        return jsonify(resp.json())


@app.route('/addFbProj', methods=["GET", "POST"])
def add_firebase_project_to_gcp():
    """Add a firebase project to your GCB Project."""

    session['redirect_to'] = "add_firebase_project_to_gcp"

    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    google.oauth2.credentials.Credentials(
        **session['credentials'])
    fb = OAuth2Session(client_id=client_secret['web']['client_id'], token=session['oauth_token'])
    form = FBForm()
    if request.method == 'GET':
        return render_template('create_fb.html', form=form)
    elif request.method == 'POST':
        # You need to enable Firebase Management API for this to work.
        # Visit : https://console.developers.google.com/apis/api/firebase.googleapis.com/overview?project=project_id
        if form.validate_on_submit():
            flash(f'Adding Firebase to GCP: {form.gcp_proj.data}')
            resp = fb.post(
                f'https://firebase.googleapis.com/v1beta1/projects/{form.gcp_proj.data}:addFirebase')
            print(f'FB Project created:{resp.json()}')
            if 'error' in resp.json().keys():
                flash(resp.json()['error'])
            return redirect('/')


@app.route('/addAndroid',  methods=["GET", "POST"])
def create_android_app():
    """Add an Android App to an FB project"""

    session['redirect_to'] = "create_android_app"

    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    google.oauth2.credentials.Credentials(
        **session['credentials'])
    fb = OAuth2Session(client_id=client_secret['web']['client_id'], token=session['oauth_token'])

    form = CreateAndroidAppForm()
    if request.method == 'GET':
        return render_template('create_app.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            flash(f'Create Android app in Firebase proj: {form.fb_proj.data}')
            resp = fb.post(
                f'https://firebase.googleapis.com/v1beta1/projects/{form.fb_proj.data}:addFirebase',
                data=json.dumps({
                    'displayName': form.display_name.data,
                    'name': form.name.data,
                    'projectId': form.fb_proj.data
                }))
            if 'error' in resp.json().keys():
                flash(resp.json()['error'])
            else:
                flash('Added Android app successfully')
            return redirect('/')


@app.route('/addIOS')
def create_ios_app():
    pass


@app.route('/authorize')
def authorize():
    """Get authorization"""

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES)

    flow.redirect_uri = url_for('callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route("/callback", methods=["GET"])
def callback():
    """Callback URL"""
    state = session['oauth_state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES,
        state=state
    )

    flow.redirect_uri = url_for('callback', _external=True)

    authorization_response = request.url
    token = flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    session['oauth_token'] = token
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for(session['redirect_to']))


if __name__ == "__main__":
    SECRET_KEY = os.urandom(24)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = SECRET_KEY
    app.run(port=8000, debug=True)