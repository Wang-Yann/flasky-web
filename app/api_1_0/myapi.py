#-*- coding:utf-8 -*-
from flask import jsonify, request, current_app, url_for
from . import api
from ..models import User, Post


# from app import csrf
from random import randint
import base64

# @csrf.exempt  #使用此装饰器屏蔽掉csrf保护，提交成功
@api.route('/avatar',methods=['GET','POST'])
def avatar():
    # if not  request.json:
        # abort(403)
    data = request.form['file'] 
    # name = request.form['name']
    # print(name)
    fname = 'av_'+str(randint(1,100))+'.jpg'
    # size = (256, 256)
    # im = Image.open(file)
    # im.thumbnail(size,Image.ANTIALIAS)
    
    # im.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname),'jpeg') 

    
    fh = open(fname, "wb")
    fh.write(base64.b64decode(data))
    fh.close()   
        
    
    # img={
        # 'token':data['csrfToken'],
        # 'data':data.get('data',''),
        # 'done':False
    
    
    # }
    
    return jsonify({'img':'img'}),200



