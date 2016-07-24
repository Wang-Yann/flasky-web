# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField,FileField, HiddenField
from wtforms.validators import Required, Length, Email, Regexp,Optional
from wtforms import ValidationError
from flask.ext.pagedown.fields import PageDownField
from ..models import Role, User,Category
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
    file=FileField(u"选择图片",validators=[])

    submit = SubmitField("Send")

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


class PostForm(Form):
    title=StringField(u"标题",validators=[Required()])
    body = PageDownField("What's on your mind?", validators=[Required()])
    category_id = SelectField(u"博文类型",coerce=int,validators=[Required()])
    tags=StringField(u"标签")
    submit = SubmitField( 'Submit')

class EditForm(Form):
    id = HiddenField('new')
    title = TextAreaField(u'标题', validators=[Required()])
    body = PageDownField(u'内容', validators=[Required()])
    
    
    tags = StringField(u'标签')
    private = BooleanField(u'不公开')
    submit = SubmitField(u'完成')
    category_id = SelectField(u"博文类型",coerce=int,validators=[Required()])
    # def new_category_validator(form, field):
        # if form.category_id.data == 'new':
            # if not len(field.data):
                # raise ValidationError(u'在此输入新分类名')
            # elif field.data in [c[1] for c in form.category_id.choices]:
                # raise ValidationError(u'分类名已存在')
	
    category_new = StringField('')
    # startup needs to create all necessary tables before the following query operation
    
    
    # categories_e = categories.query.order_by(Category.id).all()
    # choices = [(str(c.id), c.name) for c in categories_e]
    # choices.append(('new', u'--新建分类--'))    # special category hint
    # category = SelectField(u'分类', choices=choices, validators=[Required()])
    # # the category name when create new category
    
    

class CommentForm(Form):
    name=StringField(u'昵称',validators=[Required()])
    body = StringField('Enter your comment', validators=[Required()])
    follow=StringField(validators=[Required()])
    submit = SubmitField('Submit')


class SearchForm(Form):
    search = StringField('search', validators=[Required()])
