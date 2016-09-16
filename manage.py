#-*-coding:utf-8-*-
#!/usr/bin/env python

import os
import sys
import flask_admin as admin
from flask_admin.contrib import sqla
from wtforms import validators
from app.adminviews import CommentAdmin,UserAdmin,\
    PostAdmin,FileAdminView,MyModelView,MyAdminIndexView




COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]


            
from app import create_app, db
from app.models import User,UserLikePost, Follow, Role, Permission,concern_posts,\
     Post, post_tag_ref,Comment,Category,Tag,Comment_Follow,\
     Shortmessage,Photo
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


# def is_subcg_url(url):
    # x,_,y=url.partition('/post_result/cg/')
    # if y:
        # id=y.split('#')[0]
        # return Category.query.get_or_404(int(id)).parent_id!=0
    # else:
        # return False
# app.jinja_env.tests['subcg_url'] =is_subcg_url   ##很丑废弃

app.jinja_env.globals['Comment'] = Comment
app.jinja_env.globals['Category'] =Category

# from jinja2 import Environment, FileSystemLoader jinjia2不使用flask-babel 直接导入 i18n 扩展
# from babel.support import Translations
# locale_dir = "translations"
# msgdomain = "messages"
# list_of_desired_locales = ["zh_Hans_CN", "en"]
# translations = Translations.load(locale_dir, list_of_desired_locales)
# app.jinja_env.install_gettext_translations(translations)



filepath=app.config.get('UPLOAD_FILE_PATH')  ###避免上传文件夹不存在
try:
    os.mkdir(filepath)
except OSError:
    pass



def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,\
                Permission=Permission, Post=Post, Comment=Comment,\
                UserLikePost=UserLikePost,Category=Category,Tag=Tag,\
                Shortmessage=Shortmessage,Photo=Photo,post_tag_ref=post_tag_ref)
                
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


        
        
        
@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    
    upgrade()
    
    # create user roles
    Role.insert_roles()
    Category.insert_categories()
    User.generate_fake(6)
    v=User(email='admin@vlobster.com',username="AAA",password='admin123',confirmed=True)
    u=User(email='abc@vlobster.com',username="ABC",password='123456',confirmed=True,role_id=3)
    v.role_id=2
    db.session.add(v)
    db.session.commit()
    db.session.add(u)  ####插入管理员用户
    db.session.commit()
    
    User.add_self_follows()
    # Post.generate_fake(15)
    # Comment.generate_fake(15)
    
admin=admin.Admin(app,name="LOBSTER",url='/lobster/admin',\
        index_view=MyAdminIndexView(),\
        base_template='admin/my_master.html',template_mode='bootstrap3') ####使用Flask-Admin进行后台管理
        
admin.add_view(UserAdmin(User,db.session))

admin.add_view(PostAdmin(db.session))
    ####三种式样的view注意区分
admin.add_view(MyModelView(Category,db.session))
admin.add_view(MyModelView(Tag,db.session))
admin.add_view(MyModelView(Comment,db.session))
admin.add_view(MyModelView(Shortmessage,db.session))
# admin.add_view(MyModelView(Follow,db.session))
admin.add_view(MyModelView(Role,db.session))


#########admin.add_view(MyAdminIndexView(name="mine",endpoint="extra",category="Others")) 自己添加的admin View，在安全视图未使用
admin.add_view(FileAdminView(filepath,name='StaticFiles'))    





if __name__ == '__main__':
    manager.run()

    
    
    
    



