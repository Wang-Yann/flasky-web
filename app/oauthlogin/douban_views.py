from flask.ext.login import login_user, logout_user, login_required, \
    current_user

from .. import db 
import os
from app import oauth
from . import douban_login
from ..models import User
from flask import redirect, url_for, session, request, jsonify, flash,json


douban = oauth.remote_app(
    'douban',
    consumer_key='0cfc3c5d9f873b1826f4b518de95b148',
    consumer_secret='3e209e4f9ecf6a4a',
    base_url='https://api.douban.com/',
    request_token_url=None,
    request_token_params={'scope': 'douban_basic_common,shuo_basic_r'},
    access_token_url='https://www.douban.com/service/auth2/token',
    authorize_url='https://www.douban.com/service/auth2/auth',
    access_token_method='POST',
)


@douban_login.route('/')
def index():
    if 'douban_token' in session:
        resp = douban.get('shuo/v2/statuses/home_timeline')
        return jsonify(status=resp.status, data=resp.data)
    return redirect(url_for('.login'))


@douban_login.route('/login')
def login():
    return douban.authorize(callback=url_for('.authorized', _external=True))


@douban_login.route('/logout')
def logout():
    session.pop('douban_token', None)
    return redirect(url_for('.index'))


@douban_login.route('/login/authorized')
def authorized():
    resp = douban.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['douban_token'] = (resp['access_token'], '')
    me = github.get('user')
       
    return jsonify(me.data)
    
    return redirect(url_for('.index'))


@douban.tokengetter
def get_douban_oauth_token():
    return session.get('douban_token')










 

    


