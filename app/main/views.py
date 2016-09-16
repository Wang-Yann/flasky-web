# -*- coding:utf-8 -*-
import sys  
reload(sys)  
sys.setdefaultencoding('utf-8')


import os
from PIL import Image
import base64    ###图片数据传输

from datetime import datetime
from flask import render_template, redirect, url_for, abort, flash, request,json,\
    current_app, make_response,  g ,jsonify,send_from_directory  ##+++session
    
from flask_security import current_user,login_required
from flask.ext.sqlalchemy import get_debug_queries

from sqlalchemy import or_,and_

from . import main 

from .forms import EditProfileForm, EditProfileAdminForm, \
    CommentForm,SearchForm,EditForm,SMSForm,allowed_file
from .. import db 
from ..models import Permission, Role, User, Post, Comment,Comment_Follow,Category,Tag,\
    UserLikePost,Shortmessage,\
    str_to_obj,sms_types,sms_status
from ..decorators import admin_required, permission_required
from werkzeug.utils import secure_filename

from app import babel
from flask.ext.babel import gettext as _, ngettext,lazy_gettext







@babel.localeselector
def get_locale():
    # # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user.is_authenticated:
        return user.locale
    return request.accept_languages.best_match(['en','zh_TW', 'zh_CN' ])
    # ov=request.args.get('lang')  #####不用设置，使用session的形式更好
    # if ov:
        # session["lang"]=ov
    # return session.get("lang","zh")
@babel.timezoneselector
def get_timezone():
    return 'UTC+8'
    #return request.accept_languages.best_match(['es', 'zh_CN', 'en','da'])


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response

@main.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
        db.session.remove()
    #####db.session.close() 此处注意


@main.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = get_locale() 
    g.timezone = get_timezone()    
       
@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

@main.route('/')
def index():
    by=request.args.get('by','all')
    
    if by=='read_count': 
        query=Post.query.order_by(Post.read_count.desc())
    elif by=='popularity':
        query=Post.query.order_by(Post.popularity.desc())
    else:
        query=Post.query.order_by(Post.timestamp.desc())
  
    page = request.args.get('page', 1, type=int)

    pagination = query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', posts=posts,by=by,
                         pagination=pagination)
                         
                         
                         

@main.route('/explore/<username>', methods=['GET', 'POST'])
@login_required
def explore(username):
    user = User.query.filter_by(username=username).first_or_404()
    by=request.args.get('by')
    
    show_followed = False
    
    show_followed = bool(request.cookies.get('show_followed', ''))
    if by == 'show_followed':
        query = user.followed_posts        
    elif by == 'concerns':
        query = user.concerns
    elif by == 'votes':
        query=Post.query.join(UserLikePost,UserLikePost.user_id==user.id)\
                .filter(UserLikePost.post_id==Post.id)
    else:
        query=Post.query.order_by(Post.timestamp.desc())
    
    page = request.args.get('page', 1, type=int)

    pagination = query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('explore.html', posts=posts,by=by,user=user,
                         pagination=pagination)                         
                         



@main.route('/search', methods = ['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
         return redirect(url_for('.index'))
    return redirect(url_for('.post_result', parameter='search_results',value = g.search_form.search.data))


                         
@main.route('/post_result/<parameter>/<value>', methods=['GET', 'POST'])
def post_result(parameter,value):
    if parameter=='cg':
        category=Category.query.get_or_404(value)
        posts=category.category_posts
        args=[]
        if category.parent_id==0:
            args.append(category)
            subcgs=Category.query.filter(Category.parent_id==value).all()
            args.append(subcgs)
        else:
            parent_cg=Category.query.filter(Category.id==category.parent_id).first_or_404()
            args.append(parent_cg)
            
            args.append([category])
            print(args)
    elif parameter=='tag':
        current_tag=Tag.query.get_or_404(value)
        posts=current_tag.posts
        args=u'标签:'+current_tag.tag_name
    elif parameter=='timestamp':
        year,month=value.split('-')
        month1=str(int(month)+1)
        date0=datetime.strptime(year+'-'+month, '%Y-%m')
        date1=datetime.strptime(year+'-'+month1, '%Y-%m')
        posts=Post.query.filter(Post.timestamp.between(date0,date1))
        args=u'归档:'+value
    elif parameter=='search_results':
        posts=Post.query.whoosh_search(value, current_app.config['MAX_SEARCH_RESULTS'])
        args=u'搜索结果:'+value
    else: 
        posts=Post.query.filter_by(parameter=value)
        args=''
    page = request.args.get('page', 1, type=int)
    pagination = posts.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    
    
    return render_template('post_result.html', posts=posts,parameter=parameter,\
                            value=value,args=args,pagination=pagination)                        
                         
@main.route('/all')                             #####本可以去掉，为增加多样性保留
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


       
                        
                        
                        
                        
                        
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)

 

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FILE_PATH'],
                               filename)
                               
@main.route('/downloads/<filename>')
def download(filename):
    if request.method=="GET":
        path=os.path.join(current_app.config['UPLOAD_FOLDER'],filename)
        if os.path.isfile(path):
            return send_from_directory(current_app.config['UPLOAD_FOLDER'],filename,as_attachment=True)
        abort(404)                               
                               

   
@main.route('/edit-avatar/<username>', methods=['GET', 'POST'])
@login_required
def change_avatar(username):
    user = User.query.filter_by(username=username).first_or_404()
    print(user)
    # form = ChangeAvatarForm()
    if request.method == 'POST':
        file = request.files['file']
        print(file)
        if 'file' not in request.files:
            flash(_('No file part in request!'),"warning")
            return redirect(request.url)
        elif file.filename == '':
            flash(_('No selected file!'),"warning")
            return redirect(request.url)
        else:
            size = (256, 256)
            im = Image.open(file)
            im.thumbnail(size,Image.ANTIALIAS)
            if file and allowed_file(file.filename):
                fname = 'av_'+username+secure_filename(file.filename)[:5]+'.jpg'
                im.save(os.path.join(current_app.config['UPLOAD_FILE_PATH'],'avatar', fname),'jpeg')
                current_user.new_avatar_file = url_for('static', filename='%s/%s' % ('avatar', fname))
                db.session.add(current_user)
                db.session.commit()
                current_user.is_avatar_default = False
                flash(_('The avatar has been changed.'),'success')
                return redirect(url_for('.user', username=current_user.username))
    return render_template('change_avatar.html')









@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        current_user.locale=form.lang.data
        print(type(form.lang.data))
        db.session.add(current_user)
        db.session.commit()
        flash(_('The profile has been updated.'),'success')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    form.lang.data=current_user.locale
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash(_('The profile has been updated.'),'success')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    
    form = CommentForm(request.form,follow=-1)
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author_name=form.name.data,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()        
        followed_id=int(form.follow.data)
        if followed_id!=-1:
            followed=Comment.query.get_or_404(followed_id)
            f=Comment_Follow(follower_id=comment.id,followed_id=followed.id)
            comment.comment_type='reply'
            comment.reply_to=followed.author.username
            db.session.add(f)
            db.session.add(comment)
            
            db.session.commit()
            
        flash(_('Your comment has been published.'),'success')
        return redirect(url_for('.post', id=post.id, page=-1))
    if form.errors:
        flash(_('Comment Failed.'),'info')

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    
    post.read_count+=1
    post.update_data()
    return render_template('post.html', post=post, form=form,page=page,
                           comments=comments, pagination=pagination,endpoint='.post',\
                           id=post.id)


@main.route('/delete/post/<int:id>')
@login_required
def delete_post(id):
    post=Post.query.get_or_404(id)
    if current_user!=post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    count=post.comments.count()
    for comment in post.comments:
        db.session.delete(comment)
    deltagcount=0
    for tag in post.tags:
        if tag.posts.count()==1:
            deltagcount+=1
            db.session.delete(tag)
    db.session.delete(post)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        flash(_('Delete Failed.'),'warning')
    else:
        flash(_('Delete successfully , with %(name0)s comments and %(name1)s tags !',name0=count,name1=deltagcount),'success')
    
    return redirect(url_for('.user',username=current_user.username))

@main.route('/post_new/<username>', methods=['GET','POST'])
@login_required
def post_new(username):
    user = User.query.filter_by(username=username).first()
    form = EditForm(post=None)
    # form.category_id.choices = [(a.id, a.name) for a in Category.query.filter(Category.parent_id==0).all()]
    if  user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit(): 
        sub_category_id=int(request.form.get('sub_category_id',1))
        category_id=max(sub_category_id,form.category_id.data)
        print(category_id) 
        post = Post(title = form.title.data,
        body = form.body.data,
        private = form.private.data,
        category_id=category_id,
        author=user, 
        tags=str_to_obj(form.tags.data))
        
        db.session.add(post)
        db.session.commit()
        flash(_('Post successfully!'),'success')
        id=Post(title=form.title.data).id
        return redirect(url_for('.post',id=post.id))
           
    return render_template('edit_post.html',form=form,post=None)
    

@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def post_edit(id):
    post = Post.query.get_or_404(id)
    
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = EditForm(post=post)
    
    if form.validate_on_submit():
        sub_category_id=int(request.form.get('sub_category_id',1))
        cg_id=max(form.category_id.data , sub_category_id)
        
        post.title=form.title.data
        post.body = form.body.data
        post.category_id=cg_id
        post.tags=str_to_obj(form.tags.data)
        db.session.add(post)
        db.session.commit()
        flash(_('The post has been updated.'),'success')
        return redirect(url_for('.post', id=id))
    form.body.data = post.body
    form.title.data=post.title
    form.tags.data=post.post_tags
    form.category_id.data=post.category_id if  post.category.parent_id==0  else post.category.parent_id
       
    return render_template('edit_post.html', form=form,post=post)


    
    
    
    
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'),'danger')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash(_('You are already following this user.'),'info')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash(_('You are now following %(name)s anymore.',name=username),'success')
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'),'danger')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash(_('You are not following this user.'),'info')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash(_('You are not following %(name)s anymore.',name=username),'success')
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'),'danger')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


                           
                           
@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'),'danger')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)

@main.route('/delete/comment/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_comment(id):
    comment=Comment.query.get_or_404(id)
    post_id=comment.post_id
    db.session.delete(comment)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        flash(_('Delete Failed.'),'info')
    else:
        flash(_('Delete Successfully.'),'success')
    if request.args.get('by')=='moderate':
        page = request.args.get('page', 1, type=int)
        return redirect(url_for('.moderate',page=page))
    return redirect(url_for('.post',id=post_id))
    
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    by=request.args.get('by')
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,by=by,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    post_id=comment.post_id
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    if request.args.get('by')=='moderate':
        return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))
    return redirect(url_for('.post',id=post_id))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    post_id=comment.post_id
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    if request.args.get('by')=='moderate':
        return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))
    return redirect(url_for('.post',id=post_id))



@main.route('/concerns/<username>')
@login_required 
def concerns(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('Invalid user.'),'danger')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.concerns.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    posts=pagination.items
    
    return render_template('index.html', posts=posts,user=user, title="concerns of ",
                           endpoint='.concerns', pagination=pagination)



@main.route('/concern/<int:post_id>')
@login_required
@permission_required(Permission.FOLLOW)
def concern(post_id):
    post=Post.query.get_or_404(post_id)
    
    if current_user.is_concerning(post):
        flash(_('You have already collected it.'),'info')
    current_user.concern(post)
    flash(_('You  collected it successfully!'),'success')
    return redirect(url_for('.post', id=post_id))


@main.route('/unconcern/<int:post_id>')
@login_required
@permission_required(Permission.FOLLOW)
def unconcern(post_id):
    post=Post.query.get_or_404(post_id)
    current_user.unconcern(post)
    flash(_('You are not concerning anymore.'),'success')
    return redirect(url_for('.post', id=post_id))
    
@main.route('/vote/<int:post_id>')
@login_required
@permission_required(Permission.FOLLOW)
def vote(post_id):
    post=Post.query.get_or_404(post_id)
    current_user.remark(post)  
    post.update_data()
    return redirect(url_for('.post',id=post_id))
    




 

@main.route('/send_sms/<username>',methods = ['GET','POST'])
@login_required
def send_sms(username):
    user = User.query.filter_by(username=username).first()
    form=SMSForm()   ###保留记录，使用form.message_types.choices = [(value,value) for (i,value) in enumerate(sms_types)]
    if user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        rcvers=form.rcver.data 
        message_types=form.message_types.data,
        sms=Shortmessage(send_id=user.id,
        subject = form.subject.data,
        body = form.body.data,
        message_status='unread')
        print(message_types) 
        print(rcvers)
        print(rcvers=='all')
        if user.is_administrator and message_types==('all',) and rcvers=='all':
            sms.rcv_id=-1
            sms.message_types='all'
            db.session.add(sms)
            flash(_('Your message has been sended.'),'success') 
        elif  rcvers is not None:
            sms_copy=[]
            for name in rcvers.split(';'):
                rcver=User.query.filter_by(username=name).first_or_404()
                sms_copy.append(
                        Shortmessage(send_id=user.id,rcv_id=rcver.id,\
                            subject=form.subject.data,\
                            message_types=form.message_types.data,\
                            body=form.body.data,message_status='unread'))
            db.session.add_all(sms_copy)
            db.session.commit()
            flash(_('Your message has been sended.'),'success')
        else:            
            return redirect(url_for('.send_sms', form=form,username=username))
    return render_template('send_sms.html', form=form,username=username)
    
@main.route('/smsbox/<username>',methods = ['GET','POST'])
@login_required
def smsbox(username):
    by=request.args.get('by')
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    if by=='inbox':
        query= Shortmessage.query.filter\
            (or_(Shortmessage.rcv_id==user.id,Shortmessage.rcv_id==-1))
    elif by=='outbox':
        query= Shortmessage.query.filter_by(send_id=user.id)
    else:
        return redirect(url_for('.send_sms',username=username))
    
    pagination = query.paginate(
            page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    sms = pagination.items
    return render_template('smsbox.html',sms=sms,page=page,username=username,
                           pagination=pagination, by=by,endpoint='.smsbox')
    
    
    

   
    
    
    
@main.route('/alipay')
def alipay():  
    return render_template('alipay.html')
@main.route('/aboutme')
def aboutme():  
    return render_template('aboutme.html')
    
    
    
    
    
    
    
    


