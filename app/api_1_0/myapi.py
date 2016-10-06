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

# @csrf.exempt  #使用此装饰器屏蔽掉csrf保护，也可提交
@api.route('/avatar',methods=['GET','POST'])
def avatar():
    data = request.form['file'] 
    
    username= current_user.username
    time=datetime.utcnow().strftime('%y%m%d_%H%M')
    fname=username+'_'+str(time)+'.jpg'
    filepath = os.path.join(current_app.config['UPLOAD_FILE_PATH'],'avatar', fname)
        
    
    
    with open(filepath, "wb") as fh:
        fh.write(base64.b64decode(data))
     

    
    current_user.new_avatar_file = url_for('static', filename='%s/%s' % ('avatar', fname))
    db.session.add(current_user) 
    db.session.commit()
    return jsonify({'img':'img'}),200  #使用REST框架时使用，此处不需要
    
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
        db.session.commit()
    return jsonify({'id':id,'status':status,}),200
    



