#-*- coding:utf-8 -*-

from flask import Blueprint
import collections 


main = Blueprint('main', __name__)



from . import views, errors
from ..models import Permission,Category,Tag,Post,Comment,User


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
    
@main.app_context_processor
def fill_sidebar_data():
    sidebar_data={
        'category':collections.OrderedDict(),
        'archieve':collections.OrderedDict(),
        'tags':[],
        'popular':[],
        'visitors':[],
        'newcomments':[],
        'links':[],
        }

    categories = Category.query.order_by(Category.id).all()
    for category in categories:
        sidebar_data['category'][category] = len(category.posts.all())
        
    posts=Post.query.order_by(Post.timestamp.desc()).all()
    year=month=-1
    for post in posts:
        if post.timestamp.year!=year:
            year=post.timestamp.year
            sidebar_data['archieve'][year]=collections.OrderedDict()
        if post.timestamp.month!=month:
            month=post.timestamp.month
            sidebar_data['archieve'][year][month]=0
        sidebar_data['archieve'][year][month]+=1 
        
    tags_cache = Tag.query.all()
    tags_data = [(tag.id,tag.tag_name, tag.posts.count()) for tag in tags_cache]
    tags_nums = [t[2] for t in tags_data]
    tags_nums.sort()
    if len(tags_nums):
        tags_data.insert(0, (0,tags_nums[0], tags_nums[-1],))
    else:
        tags_data.insert(0, (-1, -1,-1))
    sidebar_data['tags'] = tags_data
    
    posts.sort(key=(lambda a: a.popularity), reverse=True)
    sidebar_data['popular'] = posts[:5]
    
    comments=Comment.query.order_by(Comment.timestamp.desc())
    sidebar_data['newcomments']=comments[:5]
    
    visitors=User.query.order_by(User.last_seen.desc())
    sidebar_data['visitors'] = visitors[:6]
    
     
    return dict(sidebar_data=sidebar_data)






