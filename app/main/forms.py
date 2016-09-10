# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField,FileField, HiddenField
from wtforms.validators import Required, Length, Email, Regexp,Optional
from wtforms import ValidationError
from flask.ext.pagedown.fields import PageDownField
from ..models import Role, User,Category,Post,sms_types
from .. import db

class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')
    
class ChangeAvatarForm(Form):
    pass
    # file=FileField(u"选择图片",validators=[])

    # submit = SubmitField("Send")

    
    
    
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


# class PostForm(Form):
    # title=StringField(u"标题",validators=[Required()])
    # body = PageDownField("What's on your mind?", validators=[Required()])
    # category_id = SelectField(u"博文类型",coerce=int,validators=[Required()])
    
   
    
    # tags=StringField(u"标签")
    # submit = SubmitField('Submit')
    
    
class SMSForm(Form):
    message_types=SelectField(u'类型',choices=zip(sms_types,sms_types))
    rcver=StringField(u'收件人')
    subject=StringField(u'主题',validators=[Required()])
    body = PageDownField(u"内容", validators=[Required()])
    submit = SubmitField('send')
    def validate_rcver(self, field):
       users=field.data
       if users=='all':
               pass
       else:
           for name in users.split(';'):
               user=User.query.filter_by(username=name).first() 
               if user is None:
                   raise ValidationError('请填写正确的收件人名称')
       
    
    
class EditForm(Form):
    # types = HiddenField('new')
    title = TextAreaField(u'标题', validators=[Required()])
    body = PageDownField(u'内容', validators=[Required()])
    category_id = SelectField(u"博文类型",coerce=int)
    
    tags = StringField(u'标签')
    private = BooleanField(u'不公开')
    submit = SubmitField('Submit')
    def __init__(self, post,*args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(a.id, a.name) for a in Category.query.filter(Category.parent_id==0).all()]
        self.category_id.choices.insert(0,('-1','--请选择类型--'))
        self.post = post
    def validate_title(self, field):
        
        if self.post is  None:
            if Post.query.filter_by(title=field.data).first():
                raise ValidationError(u'已存在同名文章，请修改文章标题')
        else:
            if field.data != self.post.title and Post.query.filter_by(title=field.data).first():
                raise ValidationError(u'已存在同名文章，请修改文章标题')
 


class CommentForm(Form):
    name=StringField(u'昵称',validators=[Required()])
    body = TextAreaField('Enter your comment', validators=[Required()])
    follow=StringField(validators=[Required()])
    submit = SubmitField('Submit')


class SearchForm(Form):
    search = StringField('search', validators=[Required()])
    