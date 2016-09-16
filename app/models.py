# -*- coding:utf-8 -*-

from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
from jieba.analyse import ChineseAnalyzer

from sqlalchemy import or_,and_             ###引入sqlalchemy查询函数

from flask.ext.pagedown import PageDown
import bleach
from flask import current_app, request, url_for
from flask.ext.login import  AnonymousUserMixin,UserMixin
from app.exceptions import ValidationError

try:
    import enum 
except ImportError:                 ###数据库引入enum类型
    enum = None
from . import db, login_manager


import flask_whooshalchemyplus
import sys  ####app,
if sys.version_info >= (3, 0):                                              
      enable_search = False
else:
      enable_search = True
      import flask.ext.whooshalchemy as whooshalchemy   ###whooshalchemyplus是whooshalchemy升级修改版
      
      
      
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
    def __unicode__(self):
        return self.name


class UserLikePost(db.Model):     ###为点赞功能单独添加一表浪费，但是这是试验；此表无任何关联联结，使用必须直接查询
    __tablename__='userlikepost'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer)
    post_id=db.Column(db.Integer)



class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    

concern_posts=db.Table('concern_posts',
    db.Column('user_id',db.Integer,db.ForeignKey('users.id')),
    db.Column('post_id',db.Integer,db.ForeignKey('posts.id')))         #######用户收藏文章关联表





class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    
    locale=db.Column(db.String(20),default='en')
    timezone=db.Column(db.String(30),default='UTC+8')
    
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    new_avatar_file=db.Column(db.String(64))
    
    sendsms=db.relationship('Shortmessage',backref='sender',lazy='dynamic')
    # rcv_sms=db.relationship('Shortmessage'###,foreign_keys='Shortmessage.rcv_id')
  
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
                             
    
    def remark(self,post):
        if not self.is_remarking(post):
            r=UserLikePost(user_id=self.id,post_id=post.id)
            db.session.add(r)                            
                                   
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
#
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
        if self.role is None:  ############
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
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar'
            else:
                url = 'http://www.gravatar.com/avatar'
            hash = self.avatar_hash or hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
    
    @property
    def portrait(self):
        if self.new_avatar_file:
            return self.new_avatar_file
        elif self.avatar_hash:
            return self.gravatar()
        else:
            return '/static/images/test001.jpg'
 
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

    def to_json(self):                    ###############api接口以后修改
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
    
    
    @staticmethod                    ###############api接口以后修改
    def from_json(data):
        username = data['login']
        name=data['name']
        email=data['email']
        location=data['location']
        about_me=data['url']
        if email is None or email == '':
            raise ValidationError('User does not have an email')
        return User(email=email,username=username,name=name,location=location,about_me=about_me,confirmed=True)
    
    
    
    
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
    def __unicode__(self): 
        return self.username

class AnonymousUser(AnonymousUserMixin):  
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False
    def is_concerning(self,post):
        return False
    def is_remarking(self,post):
        return False
       
login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  
    


post_tag_ref=db.Table('post_tag_ref',db.Model.metadata,
       db.Column('post_id',db.Integer,db.ForeignKey('posts.id')),
       db.Column('tag_id',db.Integer, db.ForeignKey('tags.id')))  ###############文章,标签关联表


class Post(db.Model):
    __tablename__ = 'posts'

    __searchable__ = ['title','body']                         #####whooshalchemy及plus的博文全文搜索字段
    __analyzer__=ChineseAnalyzer()                              #####jieba中文分词,为支持博文全文搜索,没深入研究,感觉没那么好用
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(128),unique=True,index=True)
    body = db.Column(db.UnicodeText)
    body_html = db.Column(db.UnicodeText)
    body_pre = db.Column(db.UnicodeText)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    read_count = db.Column(db.Integer,default=0)
    
    popularity = db.Column(db.Integer)                  ####为支持博文排名增加的简单属性
    private = db.Column(db.Boolean)                     # non-public, or hidden
    comments = db.relationship('Comment', backref='post',lazy='dynamic')
    category_id = db.Column(db.Integer,db.ForeignKey('categories.id'),default=1)  ###博文目录,default=1为未分类
    tags = db.relationship('Tag', secondary=post_tag_ref,
                             backref=db.backref('posts',lazy='dynamic'))
    
     
    
    def update_data(self):
        self.popularity=2*self.comments.count()+self.read_count+4*self.remark_count
        db.session.add(self)
        db.session.commit()
    
    @property
    def remark_count(self):
        return UserLikePost.query.filter_by(post_id=self.id).count()

    

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
        for tag in self.tags:
            r=r+tag.tag_name+' '
        return r
    @property    
    def concern_users(self):
        return self.users.all()
   
 
    @staticmethod
    def delete(post):
        for comment in post.comments:
            db.session.delete(commit)
            db.session.commit()
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        cg_count = Category.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(2, 7)),
                     title=forgery_py.lorem_ipsum.title(),
                     timestamp=forgery_py.date.date(True),
                     category_id=randint(1, cg_count),
                     read_count=randint(10, 40),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        markdown_exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', ]
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
                'img': ['alt', 'src', 'title'],}   ####为支持博文 图文 和代码高亮 修改markdown设置
        allowed_styles = ['*']
        target.body_html = bleach.linkify(bleach.clean(\
                markdown(value, output_format='html5',extensions=markdown_exts,\
                extension_configs=markdown_exts_configs),\
                tags=allowed_tags,attributes=allowed_attrs,strip=True))

        lines = target.body_html.split("\n")
        target.body_pre = "\n".join(lines[:20])   ####博文预览字段，也可以前端使用truncate函数截断
         
        # target.body_html = bleach.linkify(bleach.clean(
            # markdown(value, output_format='html'),
            # tags=allowed_tags,attributes=allowed_attrs,strip=True))

    def to_json(self):          ####api未更新
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
    def from_json(json_post):                           ####api未更新
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)

db.event.listen(Post.body, 'set', Post.on_changed_body)



class Comment_Follow(db.Model):                ####评论盖楼关联表，本来想实现网易一样盖高楼功能，后来只是简单回复显示，小菜大用；感觉前端实现盖楼更OK
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
    comment_type=db.Column(db.String(80),default='comment')           ####评论盖楼用字段
    reply_to=db.Column(db.String(128),default='notReply')
    

    followed = db.relationship('Comment_Follow',                             ####评论之间的关联关系，为了此还把评论设为jinja全局变量，此处可大改
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
        return self.followed.count()!=0
            
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        
        post_count = Post.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p= Post.query.offset(randint(0,post_count - 1)).first()
            c= Comment(body=forgery_py.lorem_ipsum.sentences(randint(2, 6)),
                     timestamp=forgery_py.date.date(True),
                     author_id=randint(0, user_count - 1),
                     post=p)
            db.session.add(c)
            db.session.commit()

    def gravatar(self, size=40, default='identicon', rating='g'):
    ####    if self.is_avatar_default: 
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar'
            else:
                url = 'http://www.gravatar.com/avatar'
            hash = self.avatar_hash or hashlib.md5(
                self.author.email.encode('utf-8')).hexdigest()
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(\
                url=url, hash=hash, size=size, default=default, rating=rating)
            
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):            
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong','img']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
    def to_json(self):                                                   ####api未更新
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
    def __unicode__(self):
        return self.body
db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Tag(db.Model):
    __tablename__='tags'  
    id = db.Column(db.Integer, primary_key= True)
    tag_name = db.Column(db.String(80),unique=True)  
    
    def __repr__(self):
        return '<Tag %r>' % self.tag_name
    def __unicode__(self):
        return self.tag_name 
    

def str_to_obj(tagstr):           #####字符串解读成标签对象
   r = []
   for tag in set(tagstr.split()):    ###此处遗漏split() ,一直失败
       tag_obj = Tag.query.filter_by(tag_name=tag).first()### 此次修改一次 first_or_404
       if tag_obj is None:
           tag_obj = Tag(tag_name=tag)
       r.append(tag_obj)
   return r

   
   
   
post_categories ={
        u"Web开发/Web":[u"Flask",u"Jinja2",u"WSGI",u"MVC/REST",u"Django",u"Tornado",u"脚本",],
        u"工具/Tools":[u"Git",u"Vim/Emacs",u"FireBug",u"Ubuntu",u"GNU/Linux", u"VisualStudio",u"Eclipse",],
        u"程序语言/Programming":[u"Python",u"Python3",u"C/C++",u"Lisp/Scheme",u"Java",u"C#",],

        u"数据库/DataBase":[u"SQLAlchemy",u"MySQL",u"SQLite",u"Redis",u"MongoDB",u"设计性能"],
        u"前端/Views":[u"HTML/CSS",u"JQuery/JS",u"Bootstrap",u"XML",u"浏览器",u"杂项",],
        u"网络基础/Internet":[u"TCP/IP",u"HTTP",u"Json/Ajax",u"PHP/ASP",u"Node.js",u"网络安全",u"大数据",],
        
        u"算法/Algorithm":[u"数据结构",u"算法基础",u"图形图像",u"机器学习",u"模式识别",u"Regex",u"GIS",u"Matlab",],
        u"计算机/Computer":[u"Windows",u"硬件系统",u"编译原理",u"程序构造",u"软件工程",],
 
        u"生活/Life":[u"新闻",u"科技",u"社会",u"工作",u"统计学",u"数学",u"读书",],
        u"移动开发/Mobile":[u"Andriod",u"IOS",u"基础"],}   
   


class Category(db.Model):
    __tablename__='categories'
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(80),unique=True)
    
    name_en = db.Column(db.String(80))
    posts = db.relationship('Post',backref='category',lazy='dynamic')
    
    parent_id =db.Column(db.Integer,default=0)   ####一级目录，为支持表单二级联动试验添加，可改进
    
    @property
    def siblings(self):
        if self.is_subcategory:
            return Category.query.filter(Category.parent_id==self.parent_id).all()
    
    @property
    def is_subcategory(self):
        return self.parent_id!=0
    @property
    def subcategories(self):
        if not self.is_subcategory:
            return Category.query.filter_by(parent_id=self.id).all()   
    @staticmethod
    def insert_categories():
        deafult_cg=Category(name=u"未分类",name_en="Unsorted",parent_id=0)
        db.session.add(deafult_cg)
        db.session.commit() 
        for key,value in post_categories.items():
            name,name_en=key.split("/")
            category = Category(name=name,name_en=name_en,parent_id=0)
            db.session.add(category)
            db.session.commit() 
            for n in value:
                subcategory = Category(name=n,parent_id=category.id)
                db.session.add(subcategory)
                db.session.commit() 
    @property
    def category_posts(self):
        if self.parent_id==0:
            sub_categories=Category.query.filter(Category.parent_id==self.id).all()
            s=[self.id]
            for sub_category in sub_categories:
                s.append(sub_category.id)
            result=Post.query.filter(Post.category_id.in_(s))
            return result
        else:
            return Post.query.filter(Post.category_id==self.id)
    def __repr__(self):
        return '<Category %r>' % self.name
    def __unicode__(self):
        return self.name



        
class sms_status(enum.Enum):   ####两种enum类型
    read = "read"
    unread = "unread"
    delete = "delete"
sms_types=('private','public','all')
            
        
class Shortmessage(db.Model):
    __tablename__='shortmessages'
    id= db.Column(db.Integer,primary_key=True)           
    
    send_id=db.Column(db.Integer,db.ForeignKey('users.id'))     ####+++++站内信也是简单实现，没考虑存储空间等；站内通告使用rcv_id==-1表示
    rcv_id=db.Column(db.Integer)
    
    subject= db.Column(db.String(80))
    body= db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_status= db.Column('status',db.Enum("read","unread","delete"),default='unread')
    message_types = db.Column('types',db.Enum(*sms_types), default='public')  
    @property
    def rcver(self):
        if self.rcv_id==-1:
            return u'全体成员'
        else:
            return User.query.get_or_404(self.rcv_id).username
    
    
    def __repr__(self):
        return '<Shortmessage %r>' % self.id
    def __unicode__(self):
        return self.subject

class Photo(db.Model): #######本来要保存头像图片，后保存在avatar，未使用本表单
    __tablename__ = 'photoes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True, index=True, nullable=False)
    description = db.Column(db.UnicodeText)
    path = db.Column(db.Unicode(256), nullable=False) # stored in local directory instead

    def __repr__(self):
        return '<Photo r%>' % self.name
    def __unicode__(self):
        return self.name










