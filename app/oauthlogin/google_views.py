from flask.ext.login import login_user, logout_user, login_required, \
    current_user

from .. import db 
import os,app
from app import oauth
from . import google_login
from ..models import User
from flask import redirect, url_for, session, request, jsonify, flash,json

google = oauth.remote_app(
    'google',
    consumer_key="34212163293-1b6l981iuh96vthq176o4ng55bhqg890.apps.googleusercontent.com",
    consumer_secret="pBz0mULyUdL2rr3nUsmKpFeC",
    request_token_params={
        'scope': 'email'
    },
       
    base_url='https://accounts.google.com/o/oauth2/v2/auth',#######'https://www.googleapis.com/oauth2/v1/'
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)
#############google  not callback

@google_login.route('/')
def index():
    if 'google_token' in session:
        me = google.get('userinfo')
        return jsonify({"data": me.data})
    return redirect(url_for('.login'))


@google_login.route('/login')
def login():
    return google.authorize(callback=url_for('.authorized', _external=True)) ####, next=request.args.get('next') or request.referrer or None


@google_login.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('main.index'))


# @google_login.route('/login/authorized')
# def authorized():
    # resp = google.authorized_response()
    # if resp is None:
        # return 'Access denied: reason=%s error=%s' % (
            # request.args['error_reason'],
            # request.args['error_description']
        # )
    # session['google_token'] = (resp['access_token'], '')
    # me = google.get('userinfo')
    # return jsonify({"data": me.data})

@google_login.route('/login/authorized')
def authorized():
    print 'In authorized()'
    resp = google.authorized_response()#####cannot run normally!!!

    print 'Printing response'
    print resp

    if resp is None:
        print 'Access denied.'
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )

    print 'Access granted!'

    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    return jsonify({'data': me.data})    
    
      

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')























 

    


