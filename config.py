#-*- coding:utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.sina.com'
    MAIL_PORT = 25
    #MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = 'VLOBSTER_:'
    FLASKY_MAIL_SENDER = os.environ.get('MAIL_USERNAME')
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    FLASKY_POSTS_PER_PAGE = 20
    FLASKY_FOLLOWERS_PER_PAGE = 50
    FLASKY_COMMENTS_PER_PAGE = 30
    FLASKY_SLOW_DB_QUERY_TIME=0.5
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY')
    WTF_I18N_ENABLED=True
    
    UPLOAD_FOLDER =basedir+'/app/static/files'
    WHOOSH_BASE = basedir+'/Index'
    MAX_SEARCH_RESULTS = 50
   
    UPLOAD_FILE_PATH=basedir+'/app/static/' 
    
    BABEL_DEFAULT_LOCALE = "en" ##"zh_Hans_CN"
    BABEL_DEFAULT_TIMEZONE='UTC+8'   
    ##WTF_CSRF_ENABLED=False #############可使用此变量取消csrf保护
    ####flask-openid登陆     
    OPENID_PROVIDERS = [
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com/', 'logo':'yahoo_logo.png'},
    {'name':'steam', 'url':'https://steamcommunity.com/openid/', 'logo':'steam_logo.png'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>', 'logo':'aol_logo.png'}       
    ]

    ###分享网站
    SHARE_LINKS = [
    {'name': "Stackoverflow", 'url': "https://stackoverflow.com/questions/tagged/python"},
    {'name': "ActiveState Code ", 'url': "http://code.activestate.com/recipes/langs/python/"},
        
    {'name':"Flask文档", 'url':"http://flask.pocoo.org/docs/0.11/"},
    {'name':"Pallets Projects(Python web)", 'url':"https://www.palletsprojects.com/"},
    
    {'name':"Python官网", 'url':"https://www.python.org/"},
    {'name': "PyPI", 'url': "https://pypi.python.org/pypi"},
    {'name': "SQLAlchemy文档", 'url': "http://docs.sqlalchemy.org/en/latest/"},
    
    {'name':"Bootstrap", 'url':"http://v3.bootcss.com/"},
    {'name':"菜鸟教程", 'url':"http://www.runoob.com/"},
    {'name': "W3School", 'url': "http://www.w3school.com.cn/h.asp"},
    {'name':"极客学院", 'url':"http://wiki.jikexueyuan.com/list/back-end/"},
    
    {'name':"开源中国", 'url':"http://www.oschina.net/project/lang/25/python"},
    {'name':"CSDN博客", 'url':"http://blog.csdn.net/"},
    {'name':"脚本之家", 'url':"http://www.jb51.net/"},
    {'name': "博客园", 'url': "http://www.cnblogs.com/"},
    {'name':"知乎", 'url':"https://www.zhihu.com/topic/19554298/hot"},
    {'name':"Linux公社", 'url':"http://www.linuxidc.com/Linuxit/"},
    
    {'name': "张鑫旭网站", 'url': "http://www.zhangxinxu.com/wordpress/category/js/"},
    {'name': "廖雪峰教程", 'url': "http://www.liaoxuefeng.com/"},
    {'name':"萧景陌专栏", 'url':"https://zhuanlan.zhihu.com/xiao-jing-mo"},
 
    {'name': "Yann's Github", 'url': "https://github.com/Wang-Yann"},
    {'name':"冬炼三九的微博", 'url':"http://weibo.com/vlobster"},
         
    ]
    
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    ##or \
        ###'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig
}
