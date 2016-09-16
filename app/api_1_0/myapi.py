#-*- coding:utf-8 -*-
import os
from flask import jsonify, request, current_app, url_for 
from . import api

from ..models import Shortmessage
from .. import db
from datetime import datetime
from flask_security import current_user
# from app import csrf

import base64

# @csrf.exempt  #使用此装饰器屏蔽掉csrf保护，提交成功
@api.route('/avatar',methods=['GET','POST'])
def avatar():
    data = request.form['file'] 
    
    username= current_user.username
    time=datetime.utcnow().strftime('%y%m%d_%H%M%S')
    fname=username+'_'+time+'.jpg'
    filepath = os.path.join(current_app.config['UPLOAD_FILE_PATH'],'avatar', fname)
    print(filepath)
    
    
    
    fh = open(filepath, "wb")
    fh.write(base64.b64decode(data))
    fh.close() 

    
    current_user.new_avatar_file = url_for('static', filename='%s/%s' % ('avatar', fname))
    db.session.add(current_user) 
    
    return jsonify({'img':'img'}),200  #本处未使用
    
@api.route('/change_status',methods=['GET','POST'])
def change_status():
    data = request.get_json()
    print(data['id'])
    print(data['status'])
    id=data['id']
    status=data['status']
    sms=Shortmessage.query.get_or_404(id)
    print(sms)
    if sms.rcv_id==current_user.id and sms.message_status=='unread':
        sms.message_status=status
        db.session.add(sms)
    return jsonify({'id':id,'status':status,}),200
    



