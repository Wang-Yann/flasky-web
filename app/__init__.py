#-*-coding:utf-8-*-

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_wtf.csrf import CsrfProtect
from flask.ext.pagedown import PageDown
from config import config,basedir
import flask_whooshalchemyplus
# from flask.ext.babel import Babel



from flask_oauthlib.client import OAuth

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
#babel = Babel
oauth=OAuth()
csrf = CsrfProtect()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

# @babel.localeselector
# def get_locale():
    # if request.args.get('lang'):
        # session['lang'] = request.args.get('lang')
    # return session.get('lang', 'en')

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    
    csrf.init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    flask_whooshalchemyplus.init_app(app)
    # babel(app)
    oauth.init_app(app)   

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)
    
    
    
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')
    
    from .oauthlogin import github_login as github_blueprint
    app.register_blueprint(github_blueprint,url_prefix='/github_login')
    
    # from .oauthlogin import weibo_login as weibo_blueprint
    # app.register_blueprint(weibo_blueprint,url_prefix='/weibo_login')
    
    # from .oauthlogin import qq_login as qq_blueprint
    # app.register_blueprint(qq_blueprint,url_prefix='/qq_login')###国内网站好麻烦，QQ、微博都要填写个人资料申请还要上传资料申请验证，以后有时间再弄
     
    # from .oauthlogin import douban_login as douban_blueprint
    # app.register_blueprint(douban_blueprint,url_prefix='/douban_login')###豆瓣暂时关闭了apikey 申请
    
    
    from .oauthlogin import google_login as google_blueprint
    app.register_blueprint(google_blueprint,url_prefix='/google_login')##google因为网路原因不能回传
    

    return app



