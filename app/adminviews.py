#-*-coding:utf-8-*-
import flask_admin as admin



###from auth.forms import LoginForm, RegistrationForm
from flask import redirect,url_for,request,abort
from flask.ext.login import login_user,logout_user,current_user
from flask_admin import BaseView,expose,helpers
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters
from wtforms import validators
from app.models import User, Follow, Role, Permission, Post, Comment,UserLikePost,Category,Tag,Comment_Follow
from flask_admin.contrib.fileadmin import FileAdmin

#from flask_security

#####customized User model admin
class UserAdmin(sqla.ModelView):
    can_create=False
    page_size=50
    ##inline_models=[(Post,dict(form_columns=['title']))]   ##内联使用
    column_exclude_list=['id','password_hash','location','member_since','name','avatar_hash','about_me']
    column_auto_select_related=False 
    #form_extra_fields={'password':PasswordField('Password')} 
    form_ajax_refs={ "posts":{"fields":(Post.title,)} }

                    

    def __init__(self,session):
        super(UserAdmin,self).__init__(User,session)
class RoleAdmin(sqla.ModelView):
    
    can_create=False
    page_size=50

    def __init__(self,session):
        super(RoleAdmin,self).__init__(Role,session)

class CommentAdmin(sqla.ModelView):
    
    can_create=False
    page_size=50

    def __init__(self,session):
        super(CommentAdmin,self).__init__(Comment,session)

class PostAdmin(sqla.ModelView):
    can_view_details=True
    page_size=50
    column_auto_select_related=False      ######小坑，因为flask-admin默认使用join模式，所以增加这句
    #column_select_related_list=('comments','tags')
    #inline_models=('Tag',dict(form_columns=['tag_name']))
    column_list=('title','body','comments','tags')
    #column_exclude_list = ['body','body_html','update_time','popularity',]
    column_formatters=dict(comments=Post.comments)
    column_sortable_list = ( 'title',('author','author.username'),('category','category.name'),'timestamp')

    column_labels = dict(title='Title',body_pre="PreView")

    column_searchable_list = ('title',User.username,'tags.tag_name')

    column_filters = ('author_id','title','timestamp','tags',
                        filters.FilterLike(Post.title,'Fixed title',options=(('test1','Test 1'),('test2','Test 2'))))


    form_args = dict(text=dict(label='Big Text',validators=[validators.required()]))
    
    form_ajax_refs={ 'comments':{'fields':(Comment.id,Comment.body)},
                                        
                     'tags':{'fields':(Tag.tag_name,)} }

    def __init__(self,session):
        super(PostAdmin,self).__init__(Post,session)
#class CategoryView(sqla.ModelView):
 #   form_exclude_columns = ['post_id',]

class FileAdminView(FileAdmin):
    pass
####class MyView(BaseView):
####    @expose('/')
####    def index(self):
####        return self.render('admin/index.html')
####

class MyModelView(sqla.ModelView):
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.is_administrator():
            return True

        return False
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))

###    def _handle_view(self,name,**kwargs):
###        if not self.is_accessible():
###            if current_user.is_authenticated:
###                abort(403)
###            else:
###                return redirect(url_for('auth.login',next=request.url))
###
# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
#        if not current_user.is_authenticated:
#            return redirect(url_for('.login_view'))
        if not current_user.is_administrator():
             abort(403)
#   ##     return self.render('admin/index.html')
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        return redirect(url_for('auth.login'))
        # handle user login
##        form = LoginForm(request.form)
##        if helpers.validate_form_on_submit(form):
##            user = form.get_user()
##            login.login_user(user)
##
##        if current_user.is_authenticated:
##            return redirect(url_for('.index'))
##        link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
##        self._template_args['form'] = form
##        self._template_args['link'] = link
##        return super(MyAdminIndexView, self).index()
##
    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        return redirect(url_for('auth.register'))
###        form = RegistrationForm(request.form)
###        if helpers.validate_form_on_submit(form):
###            user = User()
###
###            form.populate_obj(user)
###            # we hash the users password to avoid saving it as plaintext in the db,
###            # remove to use plain text:
###            user.password = generate_password_hash(form.password.data)
###
###            db.session.add(user)
###            db.session.commit()
###
###            login_user(user)
###            return redirect(url_for('.index'))
###        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
###        self._template_args['form'] = form
###        self._template_args['link'] = link
###        return super(MyAdminIndexView, self).index()
###
    @expose('/logout/')
    def logout_view(self):
        logout_user()
        return redirect(url_for('.index'))


# Flask views
#@app.route('/')
#def index():
 #   return render_template('index.html')



