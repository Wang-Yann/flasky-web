# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField,FileField, HiddenField
from wtforms.validators import Required, Length, Email, Regexp,Optional
from wtforms import ValidationError
from flask.ext.pagedown.fields import PageDownField
from ..models import Role, User,Category,Post,sms_types
from .. import db

from flask.ext.babel import lazy_gettext as _

class NameForm(Form):
    name = StringField(_('What is your name?'), validators=[Required()])
    submit = SubmitField(_('Submit'))


class EditProfileForm(Form):
    lang=SelectField(_('Language'), coerce= str, choices=[('en','en'),('zh_CN','zh_CN'),('zh_TW','zh_TW')]) #######
    name = StringField(_('Real name'), validators=[Required(),Length(0, 64)])
    location = StringField(_('Location'), validators=[Length(0, 64)])
    about_me = TextAreaField(_('About me'))
    submit = SubmitField(_('Submit'))
    
# class ChangeAvatarForm(Form):
    # pass
    # file=FileField(u"选择图片",validators=[])
    # submit = SubmitField("Send")



ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



class EditProfileAdminForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField(_('Username'), validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          _('Usernames must have only letters, '
                                          'numbers, dots or underscores'))])
    confirmed = BooleanField(_('Confirmed'))
    role = SelectField(_('Role'), coerce=int)
    name = StringField(_('Real name'), validators=[Length(0, 64)])
    location = StringField(_('Location'), validators=[Length(0, 64)])
    about_me = TextAreaField(_('About me'))
    submit = SubmitField(_('Submit'))

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError(_('Username already in use.'))


    
    
class SMSForm(Form):
    message_types=SelectField(_('Types'),choices=zip(sms_types,sms_types))
    rcver=StringField(_('Recipients'),validators=[Required()])
    subject=StringField(_('Topic'),validators=[Required()])
    body = PageDownField(_("Body"), validators=[Required()])
    submit = SubmitField(_('Send'))
    def validate_rcver(self, field):
       users=field.data
       if users=='all':
               pass
       else:
           for name in users.split(';'):
               user=User.query.filter_by(username=name).first() 
               if user is None:
                   raise ValidationError(_('Recipient not exist.'))
       
    
    
class EditForm(Form):
    # types = HiddenField('new')
    title = TextAreaField(_('Title'), validators=[Required()])
    body = PageDownField(_('Body'), validators=[Required()])
    category_id = SelectField(_("Blog_Types"),coerce=int)
    
    tags = StringField(_('Tags'),validators=[Length(0, 64)])
    private = BooleanField(_('Private?'))
    submit = SubmitField(_('Submit'))
    def __init__(self, post,*args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(a.id, a.name) for a in Category.query.filter(Category.parent_id==0).all()]
        self.category_id.choices.insert(0,('-1',_('--Select an option--')))
        self.post = post
    def validate_title(self, field):
        
        if self.post is  None:
            if Post.query.filter_by(title=field.data).first():
                raise ValidationError(_('Title already in use,please edit the title!!'))
        else:
            if field.data != self.post.title and Post.query.filter_by(title=field.data).first():
                raise ValidationError(_('Title already in use,please edit the title!!'))
 


class CommentForm(Form):
    name=StringField(_("Nickname"),validators=[Required()])
    body = TextAreaField(_('Enter your comment'), validators=[Required()])
    follow=StringField(validators=[Required()])
    submit = SubmitField(_('Submit'))


class SearchForm(Form):
    search = StringField('search', validators=[Required()])
    