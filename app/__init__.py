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




from flask_oauthlib.client import OAuth

from flask.ext.babel import Babel
babel=Babel( )

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

oauth=OAuth()
csrf = CsrfProtect()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'



def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    csrf.init_app(app)   ####CSRF保护
    bootstrap.init_app(app)  ####支持bootstrap框架
    mail.init_app(app) 
    moment.init_app(app)       ####使用moment.js
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)   ####博文支持pagedown
    flask_whooshalchemyplus.init_app(app)   ####支持博文搜索
    babel.init_app(app)                        ####多语言和国际化
    
    oauth.init_app(app)               ####其他网站账号Oauth登陆，目前只添加git和google

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)
    
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')
    
    from .oauthlogin import github_login as github_blueprint                   #####为支持Oauth登陆添加一蓝图，以后再调整
    app.register_blueprint(github_blueprint,url_prefix='/github_login')
    
    # from .oauthlogin import weibo_login as weibo_blueprint
    # app.register_blueprint(weibo_blueprint,url_prefix='/weibo_login')
    
    # from .oauthlogin import qq_login as qq_blueprint
    # app.register_blueprint(qq_blueprint,url_prefix='/qq_login')###麻烦，QQ、微博都要填写个人资料申请并上传资料申请验证，未审核通过，以后有时间再弄
     
    # from .oauthlogin import douban_login as douban_blueprint
    # app.register_blueprint(douban_blueprint,url_prefix='/douban_login') ###豆瓣暂时关闭了apikey 申请
    
    
    from .oauthlogin import google_login as google_blueprint
    app.register_blueprint(google_blueprint,url_prefix='/google_login')  ##google因为网路原因可能不能回传
    

    return app



