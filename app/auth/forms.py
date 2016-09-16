# -*- coding:utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,TextField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
from flask.ext.babel import lazy_gettext as _

class LoginForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                              Email()])
    password = PasswordField(_('Password'), validators=[Required(), Length(1, 64)])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField(_('Log In'))
    
class OpenIDLoginForm(Form):
    ###remember_me = BooleanField('Keep me logged in')
    openid=TextField('openid',validators=[Required()])
    # submit = SubmitField('Log In')

    
    

class RegistrationForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField(_('Username'), validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField(_('Password'), validators=[
        Required(),Length(3, 16), EqualTo('password2', message=_('Passwords must match.'))])
    password2 = PasswordField(_('Confirm password'), validators=[Required(),Length(3, 16)])
    submit = SubmitField(_('Register'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(_('Username already in use.'))


class ChangePasswordForm(Form):
    old_password = PasswordField(_('Old password'), validators=[Required()])
    password = PasswordField(_('New password'), validators=[
        Required(), EqualTo('password2', message=_('Passwords must match'))])
    password2 = PasswordField(_('Confirm new password'), validators=[Required()])
    submit = SubmitField(_('Update Password'))


class PasswordResetRequestForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField(_('Reset Password'))


class PasswordResetForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField(_('New Password'), validators=[
        Required(), EqualTo('password2', message=_('Passwords must match'))])
    password2 = PasswordField(_('Confirm password'), validators=[Required()])
    submit = SubmitField(_('Reset Password'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(_('Unknown email address.'))


class ChangeEmailForm(Form):
    email = StringField(_('New Email'), validators=[Required(), Length(1, 64),
                                                 Email()])
    password = PasswordField(_('Password'), validators=[Required()])
    submit = SubmitField(_('Update Email Address'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email already registered.'))

            
            
class SearchForm(Form):
    search = StringField('search', validators=[Required()])            