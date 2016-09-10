#-*-coding:utf-8-*-
import flask_admin as admin




from flask import redirect,url_for,request,abort
from flask.ext.login import login_user,logout_user,current_user
from flask_admin import BaseView,expose,helpers
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters
from wtforms import validators
from app.models import User, Follow, Role, Permission, Post, Comment,UserLikePost,Category,Tag,Comment_Follow
from flask_admin.contrib.fileadmin import FileAdmin


#####customized User model admin
class UserAdmin(sqla.ModelView):
    
    
    can_create=True
    page_size=30
    ##inline_models=[(Post,dict(form_columns=['title']))]   ##内联使用
    column_exclude_list=['id','password_hash','location','member_since','name','avatar_hash','about_me']
    column_auto_select_related=False 
    form_ajax_refs={ "posts":{"fields":(Post.title,)} }
    def is_accessible(self):
        return current_user.is_administrator()  
    
class RoleAdmin(sqla.ModelView):
                
    can_create=True
    page_size = 30
    
    

class CommentAdmin(sqla.ModelView):
    
    can_create=False
    page_size=30
    

class PostAdmin(sqla.ModelView):
    can_create=True
    page_size=50
    column_auto_select_related=False      ######小坑，因为flask-admin默认使用join模式，所以增加这句
    #####column_select_related_list=('comments','tags')
    
    ###############column_list=('title','body')####tags,'comments'不能显示关联列
    column_exclude_list = ['body','body_html','update_time','popularity',]
    column_formatters=dict(comments=Post.comments)
    column_sortable_list = ( 'title',('author','author.username'),('category','category.name'),'timestamp')
    column_labels = dict(title='Title',body_pre="PreView")
    column_searchable_list = ('title',User.username,'tags.tag_name')
    column_filters = ('author_id','title','timestamp','tags',
                        filters.FilterLike(Post.title,'Fixed title',options=(('test1','Test 1'),('test2','Test 2'))))

    form_args = dict(text=dict(label='Big Text',validators=[validators.required()]))
    
    form_ajax_refs={ 'comments':{'fields':(Comment.id,Comment.body)},
                                        
                      'tags':{'fields':(Tag.tag_name,)} }######ajax要和column_list配合才能显示，但是使用安全视图未成功
    def is_accessible(self):
        return current_user.is_administrator() 
    def __init__(self,session):
        super(PostAdmin,self).__init__(Post,session)


class FileAdminView(FileAdmin):
    can_view_details=True
    create_modal=True
    edit_modal=True

 
    
    
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

## Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_administrator():
             abort(403)
#   ##     return self.render('admin/index.html')
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        return redirect(url_for('auth.login'))
        
    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        return redirect(url_for('auth.register'))

    @expose('/logout/')
    def logout_view(self):
        logout_user()
        return redirect(url_for('main.index'))


		






