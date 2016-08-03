#-*-coding:utf-8-*-
#!/usr/bin/env python

import os
import sys
import flask_admin as admin
from flask_admin.contrib import sqla
from wtforms import validators
from app.adminviews import CommentAdmin,UserAdmin,\
    PostAdmin,FileAdminView,MyModelView,MyAdminIndexView



##from flask_security import Security,SQLAlchemyUserDatastore
###from flask_admin import helpers as admin_helpers


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




app.jinja_env.globals['Comment'] = Comment
app.jinja_env.globals['Post'] = Post

filepath=app.config.get('UPLOAD_FILE_PATH') 
try:
    os.mkdir(filepath)
except OSError:
    pass



def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,\
                Permission=Permission, Post=Post, Comment=Comment,\
                UserLikePost=UserLikePost,Category=Category,Tag=Tag,\
                Shortmessage=Shortmessage,Photo=Photo)
                
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
    

    
    
    
    # migrate database to latest revision
    upgrade()
    
    # create user roles
    Role.insert_roles()
    Category.insert_categories()
    # create self-follows for all users
    User.generate_fake(12)
    
    u=User(email='abc@abc.com',username="abcd",password='abc',confirmed=True,role_id=2) 
    v=User(email='a@abc.com',username="a",password='abc',confirmed=True,role_id=3)
    x=User(email='b@abc.com',username="b",password='abc',confirmed=True,role_id=3)
    y=User(email='c@abc.com',username="c",password='abc',confirmed=True,role_id=3)
    db.session.add(u)
    db.session.add(v)
    db.session.add(x)
    db.session.add(y)
    db.session.commit()
    User.add_self_follows()
    Post.generate_fake(10)
    Comment.generate_fake(12)
    
    
########user_datastore=SQLAlchemyUserDatastore(db,User,Role)
####security=Security(app,user_datastore)
####
####
####
####
####@security.context_processor
####def security_context_processor():
####    return dict(
####        admin_base_template=admin.base_template,
####        admin_view=admin.index_view,
####        h=admin_helpers,
####        get_url=url_for
####        )
####
admin=admin.Admin(app,name="LOBSTER",url='/lobster/admin',\
        index_view=MyAdminIndexView(),\
        base_template='admin/my_master.html',template_mode='bootstrap3')

#admin.add_view(MyModelView(Role,db.session))









#admin.add_view(UserAdmin(User,db.session))

admin.add_view(PostAdmin(db.session))

admin.add_view(MyModelView(Comment,db.session))    ####三种式样的view注意区分

admin.add_view(MyModelView(Category,db.session))
admin.add_view(MyModelView(Tag,db.session))
admin.add_view(MyModelView(Follow,db.session))
##admin.add_view(MyView(name="yann",endpoint="extra",category="others"))
admin.add_view(FileAdminView(filepath,name='Files'))



if __name__ == '__main__':
    manager.run()


