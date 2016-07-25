#-*- coding:utf-8 -*-
import os
from PIL import Image
from datetime import datetime
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response,  g
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm,\
    CommentForm,ChangeAvatarForm,SearchForm,EditForm,allowed_file
from .. import db
from ..models import Permission, Role, User, Post, Comment,Comment_Follow,Category,Tag,UserLikePost,\
    str_to_obj,remark
from ..decorators import admin_required, permission_required
from werkzeug.utils import secure_filename
from flask import send_from_directory
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
#    db.session.close()


@main.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
       g.user.last_seen = datetime.utcnow()
       db.session.add(g.user)
       db.session.commit()
       g.search_form = SearchForm()
@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    by=request.args.get('by') or 'all'
    
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
        if by == 'show_followed':
            query = current_user.followed_posts        
        elif by == 'concerns':
            query=current_user.concerns
        elif by == 'votes':
            query=Post.query.join(UserLikePost,UserLikePost.user_id==current_user.id)\
                    .filter(UserLikePost.post_id==Post.id)
        else:
            query=Post.query.order_by(Post.timestamp.desc())
    else:
        if by=='read_count': 
            query=Post.query.order_by(Post.read_count.desc())
        elif by=='comment_count':
            query=Post.query.order_by(Post.comments.count)
        else:
            query=Post.query.order_by(Post.timestamp.desc())
        

    page = request.args.get('page', 1, type=int)
#    if show_followed:
#        query = current_user.followed_posts
#    else:
#        query = Post.query
    pagination = query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', posts=posts,by=by,
                         pagination=pagination)


@main.route('/all')
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

@main.route('/post/new', methods=['GET', 'POST'])
@login_required
def post_new():
    form = EditForm()
    form.category_id.choices = [(a.id, a.name) for a in Category.query.all()]
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        # new or edit post received
        post = Post(
        title = form.title.data,
        body = form.body.data,
        private = form.private.data,
        category_id=form.category_id.data,
        author=current_user._get_current_object(), 
        tags=str_to_obj(form.tags.data),
        read_count=0)
        db.session.add(post)
        flash(u"发表成功")
    #else:
     #   post=Post.query.get_or_404(form.id.data)
        return redirect(url_for('.post_new'))
    return render_template('edit_post.html',form=form)
        # # display new or edit page
           
            # form.category_id.choices.append(('new', u'--新建分类--'))    # special category hint

            ##if opid == 'new':
            ##    new = True
            ##    form.id.data = 'new'
            ##    form.category_id.data = '1'    # default category
            ##    return render_template('edit.html', form=form, new=True)
   #     else: 
   #        id = int(opid)
   #        post = Post.query.get_or_404(id)
   #        form.styles.data = "edit"
   #        form.title.data = post.title
   #        form.body.data = post.body
   #        form.private.data = post.private
   #        form.category_id.data = post.category_id
   #        form.tags.data=post.post_tags
   #        
   #        return render_template('edit.html', form=form)
                        
                        
                        
                        
                        
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

from flask import send_from_directory

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               filename)
##@main.route('/', methods=['GET','POST'])
##def upload_file():
##    if request.method == 'POST':
##        file = request.files['file']
##        if file and allowed_file(file.filename):
##            filename = secure_filename(file.filename)
##            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
##            return redirect(url_for('uploaded_file',
##                                   filename=filename))
##    return '''
##    <!doctype html>
##    <title>Upload new File</title>
##    <h1>Upload new File</h1>
##    <form action="" method=post enctype=multipart/form-data>
##      <p><input type=file name=file>
##         <input type=submit value=Upload>
##    </form>
##    '''
####def upload():
##    upload_file = request.files['image01']
##    if upload_file and allowed_file(upload_file.fiilename):
##        filename = secure_filename(upload_file.filename)
##        upload_file.save(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename))
##        return 'hello, '+request.form.get('name', 'little apple')+'. success'
##    else:
##        return 'hello, '+request.form.get('name', 'little apple')+'. failed'
##
@main.route('/edit-avatar/<username>', methods=['GET', 'POST'])
@login_required
def change_avatar(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = ChangeAvatarForm()
    if request.method == 'POST' and form.validate_on_submit() :
        file = request.files['file']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        elif file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        else:
            size = (256, 256)
            im = Image.open(file)
            im.thumbnail(size,Image.ANTIALIAS)
            if file and allowed_file(file.filename):
                fname = 'av_'+secure_filename(file.filename)[:7]+'r'
                im.save(os.path.join(current_app.config['UPLOAD_FOLDER'],'avatar', fname),'jpeg')
                current_user.new_avatar_file = url_for('static', filename='%s/%s' % ('avatar', fname))
                db.session.add(current_user)
                current_user.is_avatar_default = False
                flash(u'头像修改成功')
                return redirect(url_for('.user', username=current_user.username))
    return render_template('change_avatar.html',form=form)









@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
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
        flash('The profile has been updated.')
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
    post.read_count+=1
    db.session.add(post)    #######
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
            comment.reply_to=followed.author_name
            db.session.add(f)
            db.session.add(comment)
            db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    if form.errors:
        flash(u"发表评论失败")

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    #post.add_view(post,db)

    return render_template('post.html', post=post, form=form,page=page,
                           comments=comments, pagination=pagination,endpoint='.post',\
                           id=post.id)

#@main.route('/post/<int:id>', methods=['GET', 'POST'])
#def post(id):
#    post = Post.query.get_or_404(id)
#    form = CommentForm()
#    if form.validate_on_submit():
#        comment = Comment(body=form.body.data,
#                          post=post,
#                          author=current_user._get_current_object())
#        db.session.add(comment)
#        flash('Your comment has been published.')
#        return redirect(url_for('.post', id=post.id, page=-1))
#    page = request.args.get('page', 1, type=int)
#    if page == -1:
#        page = (post.comments.count() - 1) // \
#            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
#    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
#        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
#        error_out=False)
#    comments = pagination.items
#    return render_template('post.html', posts=[post], form=form,
#                           comments=comments, pagination=pagination)
#
@main.route('/delete/<int:id>')
@login_required
def delete(id):
    post=Post.query.get_or_404(id)
    if current_user!=post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    u=current_user
    db.session.delete(post)
    flash(u"你成功删除了该文章")
    return redirect(url_for('.user',username=u.username))


    
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def post_edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = EditForm()
    form.category_id.choices = [(a.id, a.name) for a in Category.query.all()]
    if form.validate_on_submit():
        post.title=form.title.data
        post.body = form.body.data
        post.category_id=form.category_id.data
        post.tags=str_to_obj(form.tags.data)
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    form.title.data=post.title
    form.tags.data=post.post_tags
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
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
        flash('Invalid user.')
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


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

@main.route('/cg/<int:id>')
def cg(id):
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(category_id=id).paginate(
            page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    return render_template('cg.html',posts=posts,
                           pagination=pagination, endpoint='.cg',id=id)

@main.route('/tag/<int:tag_id>')
def tag(tag_id):
    page = request.args.get('page', 1, type=int)
    current_tag=Tag.query.get_or_404(tag_id)
    pagination =current_tag.posts.paginate(
            page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    posts = pagination.items
    return render_template('tag.html',posts=posts,
                           pagination=pagination, endpoint='.tag',tag_id=tag_id)


@main.route('/concerns/<username>')
@login_required 
def concerns(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
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
        flash(u'你已经收藏了本文章.')
        return redirect(url_for('.post', id=post_id))
    current_user.concern(post)
    flash(u'你收藏了本文章.')
    return redirect(url_for('.post', id=post_id))


@main.route('/unconcern/<int:post_id>')
@login_required
@permission_required(Permission.FOLLOW)
def unconcern(post_id):
    post=Post.query.get_or_404(post_id)
    if not current_user.is_concerning(post):
        flash('You are not concerning this post.')
        return redirect(url_for('.post', id=post_id))
    current_user.unconcern(post)
    flash('You are not concerning anymore.')
    return redirect(url_for('.post', id=post_id))
@main.route('/vote/<int:post_id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.FOLLOW)
def vote(post_id):
    post=Post.query.get_or_404(post_id)
    if  not current_user.is_remarking(post):
#        r=UserLikePost(user_id=current_user.id,post_id=post.id)
#        db.session.add(r)
#        db.session.commit()
        remark(current_user,post)
        flash('success')
        return redirect(url_for('.post',id=post_id))
    return redirect(url_for('.post',id=post_id))



@main.route('/search', methods = ['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
         return redirect(url_for('.index'))
    return redirect(url_for('.search_results', query = g.search_form.search.data))
  #  form=SearchForm()
  #  if  form.validate_on_submit():
  #      return redirect(url_for('search_results',form=form, query = form.search.data))
  #  return redirect(url_for('index'))
  #  

@main.route('/search_results/<query>')
@login_required
def search_results(query):
#    page = request.args.get('page', 1, type=int)
    posts=Post.query.whoosh_search(query, current_app.config['MAX_SEARCH_RESULTS']).all()
#    pagination = posts.order_by(Post.timestamp.desc()).\
 #               paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],\
  #              error_out=False)

    return render_template('search_results.html',posts=posts,query=query)



