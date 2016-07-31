from flask.ext.login import login_user, logout_user, login_required, \
    current_user

from .. import db 
import os
from app import oauth
from . import github_login
from ..models import User
from flask import redirect, url_for, session, request, jsonify, flash,json


github = oauth.remote_app(
    'github',
    consumer_key='e1c0a729ad0f61811811',
    consumer_secret='07d0505feeb83f6a2dc38df29d1916ee4909e13e',
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)


@github_login.route('/')
def index():
    if 'github_token' in session:
        me = github.get('user')
        resp=jsonify(me.data)
        data=json.loads(resp.data.decode('utf-8'))
        
        user = User.query.filter_by(email=data.get('email')).first() 
        if user is None:
            user=User.from_json(data)
            db.session.add(user)
            db.session.commit()
            
        remember_me = False
        if 'remember_me' in session:
            remember_me = session['remember_me']
            session.pop('remember_me', None)
        login_user(user,remember = remember_me)
        return redirect( url_for('main.index'))
        
               
    else:   
        return redirect(url_for('.login'))


@github_login.route('/login')
def login():
    
        return github.authorize(callback=url_for('.authorized', _external=True))


@github_login.route('/logout')
def logout():
    if 'github_token' in session:
        session.pop('github_token', None)
        return redirect(url_for('.index'))


@github_login.route('/login/authorized')
def authorized():
    if 'github_token' in session:
        resp = github.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    session['github_token'] = (resp['access_token'], '')
    me = github.get('user')
       
    return jsonify(me.data)


@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')










 

    


