from flask import Blueprint





# weibo_login = Blueprint('weibo_login', __name__)
# qq_login = Blueprint('qq_login', __name__)
github_login = Blueprint('github_login', __name__)
google_login = Blueprint('google_login', __name__)

# douban_login = Blueprint('douban_login', __name__)


from . import github_views,google_views
######,weibo_views,qq_views,douban_views
