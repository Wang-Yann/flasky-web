# -*- coding:utf-8 -*-
from flask.ext.login import login_user, logout_user

from .. import db 
import os
from app import oauth
from . import weibo_login
from ..models import User
from flask import redirect, url_for, session, request, jsonify, flash,json


weibo = oauth.remote_app(
    'weibo',
    consumer_key='909122383',
    consumer_secret='2cdc60e5e9e14398c1cbdf309f2ebd3a',
    request_token_params={'scope': 'email,statuses_to_me_read'},
    base_url='https://api.weibo.com/2/',
    authorize_url='https://api.weibo.com/oauth2/authorize',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://api.weibo.com/oauth2/access_token',
    # since weibo's response is a shit, we need to force parse the content
    content_type='application/json',
)


@weibo_login.route('/')
def index():
    if 'oauth_token' in session:
        access_token = session['oauth_token'][0]
        resp = weibo.get('statuses/home_timeline.json')
        return jsonify(resp.data)
    return redirect(url_for('login'))


@weibo_login.route('/login')
def login():
    return weibo.authorize(callback=url_for('authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))


@weibo_login.route('/logout')
def logout():
    session.pop('oauth_token', None)
    return redirect(url_for('index'))


@weibo_login.route('/login/authorized')
def authorized():
    resp = weibo.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    return redirect(url_for('index'))


@weibo.tokengetter
def get_weibo_oauth_token():
    return session.get('oauth_token')


def change_weibo_header(uri, headers, body):
    """Since weibo is a rubbish server, it does not follow the standard,
    we need to change the authorization header for it."""
    auth = headers.get('Authorization')
    if auth:
        auth = auth.replace('Bearer', 'OAuth2')
        headers['Authorization'] = auth
    return uri, headers, body

weibo.pre_request = change_weibo_header







 

    


