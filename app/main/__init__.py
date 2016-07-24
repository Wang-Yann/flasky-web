from flask import Blueprint
import collections 
main = Blueprint('main', __name__)
from . import views, errors
from ..models import Permission,Category,Tag

#@main.app_context_processor
#def inject_user():
#    return dict(user=current_user)
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
@main.app_context_processor
def fill_sidebar_data():
    sidebar_data={
        'category':collections.OrderedDict(),
        'tags':[],
        'share':None
        }
    categories = Category.query.order_by(Category.id).all()
    for category in categories:
        sidebar_data['category'][category] = len(category.post_id.all())
    
    tags_cache = Tag.query.all()
    tags_data = [(tag.id,tag.tag_name, tag.posts.count()) for tag in tags_cache]
    tags_nums = [t[2] for t in tags_data]
    tags_nums.sort()
    if len(tags_nums):
        tags_data.insert(0, (0,tags_nums[0], tags_nums[-1],))
    else:
        tags_data.insert(0, (-1, -1,-1))
    sidebar_data['tags'] = tags_data
     
    return dict(sidebar_data=sidebar_data)






