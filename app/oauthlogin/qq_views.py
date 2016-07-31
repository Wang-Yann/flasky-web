from flask.ext.login import login_user, logout_user

from .. import db 
import os
from app import oauth
from . import qq_login
from ..models import User
from flask import redirect, url_for, session, jsonify, flash,json,Markup




qq = oauth.remote_app(
    'qq',
    consumer_key='1105581412',
    consumer_secret='9vKLvZAKu26O9Sbx',
    base_url='https://graph.qq.com',
    request_token_url=None,
    request_token_params={'scope': 'get_user_info'},
    access_token_url='/oauth2.0/token',
    authorize_url='/oauth2.0/authorize',
)


def json_to_dict(x):
    '''OAuthResponse class can't parse the JSON data with content-type
-    text/html and because of a rubbish api, we can't just tell flask-oauthlib to treat it as json.'''
    if x.find(b'callback') > -1:
        # the rubbish api (https://graph.qq.com/oauth2.0/authorize) is handled here as special case
        pos_lb = x.find(b'{')
        pos_rb = x.find(b'}')
        x = x[pos_lb:pos_rb + 1]

    try:
        if type(x) != str:  # Py3k
            x = x.decode('utf-8')
        return json.loads(x, encoding='utf-8')
    except:
        return x


def update_qq_api_request_data(data={}):
    '''Update some required parameters for OAuth2.0 API calls'''
    defaults = {
        'openid': session.get('qq_openid'),
        'access_token': session.get('qq_token')[0],
        'oauth_consumer_key': '1105581412',
    }
    defaults.update(data)
    return defaults


@qq_login.route('/')
def index():
    # if 'qq_token' in session:
        # me = google.get('userinfo')
        # return jsonify({"data": me.data})
    # return redirect(url_for('google_login.login'))


    '''just for verify website owner here.'''
    return Markup('''<meta property="qc:admins" '''
                  '''content="226526754150631611006375" />''')


@qq_login.route('/user_info')
def get_user_info():
    if 'qq_token' in session:
        data = update_qq_api_request_data()
        resp = qq.get('/user/get_user_info', data=data)
        return jsonify(status=resp.status, data=json_to_dict(resp.data))
    return redirect(url_for('.login'))


@qq_login.route('/login')
def login():
    return qq.authorize(callback=url_for('.authorized', _external=True))


@qq_login.route('/logout')
def logout():
    session.pop('qq_token', None)
    return redirect(url_for('.get_user_info'))


@qq_login.route('/login/authorized')
def authorized():
    resp = qq.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['qq_token'] = (resp['access_token'], '')

    # Get openid via access_token, openid and access_token are needed for API calls
    resp = qq.get('/oauth2.0/me', {'access_token': session['qq_token'][0]})
    resp = json_to_dict(resp.data)
    if isinstance(resp, dict):
        session['qq_openid'] = resp.get('openid')

    return redirect(url_for('.get_user_info'))


@qq.tokengetter
def get_qq_oauth_token():
    return session.get('qq_token')


def convert_keys_to_string(dictionary):
    '''Recursively converts dictionary keys to strings.'''
    if not isinstance(dictionary, dict):
        return dictionary
    return dict((str(k), convert_keys_to_string(v)) for k, v in dictionary.items())

 

    


