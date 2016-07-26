#!/usr/bin/env python
import os
import sys
#import flask_whooshalchemyplus
import flask_admin as admin
from flask_admin import BaseView,expose
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters
from wtforms import validators



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
from app.models import User, Follow, Role, Permission, Post, Comment,UserLikePost,Category,Tag,Comment_Follow
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

app.jinja_env.globals['Comment'] = Comment
app.jinja_env.globals['Post'] = Post

def make_shell_context():
    return dict(app=app, db=db, User=User, Follow=Follow, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment,\
                UserLikePost=UserLikePost,Category=Category)
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
    from app.models import Role, User

    # migrate database to latest revision
    upgrade()
    
    # create user roles
    Role.insert_roles()
    Category.insert_categories()
    # create self-follows for all users
    User.add_self_follows()

###customized User model admin
class UserAdmin(sqla.ModelView):
    inline_models = (User,)

class PostAdmin(sqla.ModelView):
    column_excluded_list = ['body']

    column_sortable_list = ( 'title',('author_id','author_id'),'timestamp')

    column_labels = dict(title='Post title')

    column_searchable_list = ('title',User.username,'tags.tag_name')

    column_filters = ('author_id','title','timestamp','tags',
                        filters.FilterLike(Post.title,'Fixed title',options=(('test1','Test 1'),('test2','Test 2'))))

    form_args = dict(text=dict(label='Big Text',validators=[validators.required()]))
    
   # form_ajax_refs={'user':{'fields':(User.username,User.email)},
    #                'tags':{'fields':(Tag.tag_name,)} }

    def __init__(self,session):
        super(PostAdmin,self).__init__(Post,session)
class CategoryView(sqla.ModelView):
    form_excluded_columns = ['post_id',]

class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')


admin=admin.Admin(app,name="LOBSTER",template_mode='bootstrap3')

#admin.add_view(UserAdmin(User,db.session))
admin.add_view(sqla.ModelView(Tag,db.session))
admin.add_view(PostAdmin(db.session))
admin.add_view(CategoryView(Category,db.session))
admin.add_view(MyView(name="hello 1",endpoint="test1",category="test"))




if __name__ == '__main__':
    manager.run()


