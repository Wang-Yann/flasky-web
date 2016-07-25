# -*- coding:utf-8 -*-
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
from jieba.analyse import ChineseAnalyzer

from flask.ext.pagedown import PageDown

import bleach
from flask import current_app, request, url_for
from flask.ext.login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
import app,sys
import flask_whooshalchemyplus
if sys.version_info >= (3, 0):                                              
      enable_search = False
else:
      enable_search = True
      import flask.ext.whooshalchemy as whooshalchemy 
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

####对文章的点赞
#class RemarkPost(db.Model):
#    __tablename__='remarkposts'
#    id=db.Column(db.Integer,primary_key=True)
#    owner_id=db.Column(db.Integer,db.ForeignKey('users.id'),index=True)
#    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'),index=True)
#    attitude=db.Column(db.Integer)
#    timestamp=db.Column(db.DateTime,default=datetime.utcnow)
#
####对评论的点赞
#class Remark(db.Model):
#    __tablename__='remarks'
#    id=db.Column(db.Integer,primary_key=True)
#    owner_id=db.Column(db.Integer,db.ForeignKey('users.id'),index=True)
#    comment_id=db.Column(db.Integer,db.ForeignKey('comments.id'),index=True)
#    attitude=db.Column(db.Integer)
#    timestamp=db.Column(db.DateTime,default=datetime.utcnow)
#
class UserLikePost(db.Model):   
    __tablename__='userlikepost'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer)
    post_id=db.Column(db.Integer)
    
    #timestamp = db.Column(db.DateTime, default=datetime.utcnow)
def remark(user,post):
        r=UserLikePost(user_id=user.id,post_id=post.id)
        db.session.add(r)
#        db.session.commit()
#


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


concern_posts=db.Table('concern_posts',
    db.Column('user_id',db.Integer,db.ForeignKey('users.id')),
    db.Column('post_id',db.Integer,db.ForeignKey('posts.id')))



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    new_avatar_file=db.Column(db.String(128))

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
    concerns=db.relationship('Post',secondary=concern_posts,
                                backref=db.backref('users',lazy='dynamic'),
                                lazy='dynamic')

    def is_remarking(self,post):
        return UserLikePost.query.filter(UserLikePost.user_id==self.id,\
            UserLikePost.post_id==post.id).first() is not None
##    remarks=db.relationship('Comment',
##                                secondary=Remark,
##                                backref=db.backref('users',lazy='dynamic'),
##                                lazy='dynamic',
##                                single_parent=True,
##                                cascade='all,delete-orphan')
##
##    remarkposts=db.relationship('Post',
##                                secondary=Remark,
##                                backref=db.backref('users',lazy='dynamic'),
##                                lazy='dynamic',
##                                single_parent=True,
##                                cascade='all,delete-orphan')
##
##                                


    def is_concerning(self,post):
        return self.concerns.filter_by(id=post.id).first() is not None
    def concern(self,post):
        if not self.is_concerning(post):
            self.concerns.append(post)
            db.session.add(self)
    def unconcern(self,post):
        if self.is_concerning(post):
            self.concerns.remove(post)
            db.session.commit() 
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        self.followed.append(Follow(followed=self))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
    ####    if self.is_avatar_default: 
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar'
            else:
                url = 'http://www.gravatar.com/avatar'
            hash = self.avatar_hash or hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id, _external=True),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts',
                                      id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


post_tag_ref=\
    db.Table('post_tag_ref',
       db.Column('post_id',db.Integer,db.ForeignKey('posts.id')),
       db.Column('tag_id',db.Integer, db.ForeignKey('tags.id')))


class Post(db.Model):
    __tablename__ = 'posts'

    __searchable__ = ['title','body']
    __analyzer__=ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(128),unique=True,index=True)
    body = db.Column(db.UnicodeText)
    body_html = db.Column(db.UnicodeText)
    body_pre = db.Column(db.UnicodeText)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime,index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    read_count = db.Column(db.Integer)
    
    popularity = db.Column(db.Integer)
    private = db.Column(db.Boolean) # non-public, or hidden
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    category_id = db.Column(db.Integer,db.ForeignKey('categories.id'))  ###++++
    tags = db.relationship('Tag', secondary=post_tag_ref, 
                            backref=db.backref('posts',lazy='dynamic'),
                            lazy='dynamic',
                            single_parent=True,
                            cascade='all, delete-orphan')
    
    @staticmethod
    def update_data(post,db):
        post.popularity=post.comments.count()+post.read_count+3*post.remark_count
        db.session.add(post)
        db.session.commit()
    #@property
    #def concern_users(self):
    #   return self.users.all().count()
    @property
    def remark_count(self):
        return UserLikePost.query.filter_by(post_id=self.id).count()
#    agree_count=db.Column(db.Integer,default=0)
#   against_count=db.Column(db.Integer,default=0)
    
##     
##    def remarkPost_count(self,type):
##        return RemarkPost.query.filter_by(post_id=self.id,attitude=type).count() 
##    def remark_count(self,type):
##        if type==Attitude.AGREE:
##            return self.agree_count
##        else:
##            return self.against_count   
##    def remark_it(self,type,user_id):
##        remark=Remark.query.filter_by(comment_id=self.id,owner_id=user_id).first()
##        if type==Attitude.AGREE or Attitude.AGAINST:
##            remark=Remark(comment_id=self.id,owner_id=user_id,attitude=type)
##            db.session.add(remark)
##            if type==Attitude.AGREE:
##                self.agree_count+=1
##            else:
##                self.against_count+=1  
    @property 
    def post_tags(self):
        r=''
        for tag in self.tags.all():
            r=r+tag.tag_name+' '
        return r
    @property    
    def concern_users(self):
        return self.users.all()
   
 
    @staticmethod
    def delete(post):
        for comment in post.comments:
            db.session.delete(commit)
            
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        markdown_exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 
                    ]
        markdown_exts_configs = {
                        'markdown.extensions.codehilite':
                                {
                                    'css_class': 'highlight',   # default class is 'codehilite'
                                },
                    }
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3','h4','h5','h6','p','img']
        allowed_attrs={
                '*': ['class', 'style'],
                'a': ['href', 'rel', 'title'],
                'img': ['alt', 'src', 'title'],
              }
        allowed_styles = ['*']
        target.body_html = bleach.linkify(bleach.clean(\
                markdown(value, output_format='html5',extensions=markdown_exts,\
                extension_configs=markdown_exts_configs),\
                tags=allowed_tags,attributes=allowed_attrs,strip=True))

        lines = target.body_html.split("\n")
        target.body_pre = "\n".join(lines[:20])
              
              
              
        # target.body_html = bleach.linkify(bleach.clean(
            # markdown(value, output_format='html'),
            # tags=allowed_tags,attributes=allowed_attrs,strip=True))

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
            'comments': url_for('api.get_post_comments', id=self.id,
                                _external=True),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)


db.event.listen(Post.body, 'set', Post.on_changed_body)



class Comment_Follow(db.Model):
    __tablename__ = 'comment_follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('comments.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean,default=False)
    author_name=db.Column(db.String(32))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author_email=db.Column(db.String(80))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    avatar_hash=db.Column(db.String(80))
    comment_type=db.Column(db.String(80),default='comment')
    reply_to=db.Column(db.String(128),default='notReply')
    
##    agree_count=db.Column(db.Integer,default=0)    
##    against_count=db.Column(db.Integer,default=0)    
##    remarks=db.relationship('Remark',foreign_keys=[Remark.comment_id],
##                            backref=db.backref('comment',lazy='joined'),
##                            lazy='dynamic',
##                            cascade='all,delete-orphan')
##
    followed = db.relationship('Comment_Follow',
                               foreign_keys=[Comment_Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Comment_Follow',
                                foreign_keys=[Comment_Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    def __init__(self,**kwargs):
        super(Comment,self).__init__(**kwargs)
        if self.author_email is not None and self.avatar_hash is None:
            self.avatar_hash=hashlib.md5(self.author_email.encode('utf-8')).hexdigest()
    def is_reply(self):
        # return self.followed.filter_by(followed_id=self.id).first() is not None
        return self.followed.count()!=0
            
# #   @property     
    # def follwed_name(self):
        # if self.is_reply():
            # return self.followed.author_name
    def gravatar(self, size=40, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash 
        # or hashlib.md5(
            # self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
            
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong','img']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment
    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)

db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Tag(db.Model):
    __tablename__='tags'  
    id = db.Column(db.Integer, primary_key= True)
    tag_name = db.Column(db.String(80),unique=True)  
 
   
    #@property
    #def tag_posts(self):
   #     return Post.query.join(post_tag_ref.post_id==Post.id).filter(post_tag_ref.tag_id==self.id)

def str_to_obj(tags):
   r = []
   for tag in tags.split():    ###此处遗漏split() ,一直失败
       tag_obj = Tag.query.filter_by(tag_name=tag).first()
       if tag_obj is None:
           tag_obj = Tag(tag_name=tag)
       r.append(tag_obj)
   return r



class Category(db.Model):
    __tablename__='categories'
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.Unicode(80),unique=True)
    post_id = db.relationship('Post',backref='category',lazy='dynamic')

    @staticmethod
    def insert_categories():
        categories =[u"Web技术", u"数据库", u"编程", u"生活",u"Linux"] 
        for n in categories:
            category = Category(name=n)
            db.session.add(category)
        db.session.commit() 
    @property
    def category_posts(self):
        return Post.query.filter_by(Post.category==self.id)
    def __repr__(self):
        return '<Category %r>' % self.name

















