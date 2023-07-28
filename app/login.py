import yaml
import requests
from flask import request, Blueprint
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import create_access_token
from models.coupon_finder_db_model import User
from . import coupon_finder_engine

login_bp = Blueprint("coupon", __name__, url_prefix="/login")
session = sessionmaker(bind = coupon_finder_engine)()
with open('app\config.yml') as f:
    config = yaml.safe_load(f)

@login_bp.route('', methods=['POST'])
def login():
    # 假设这里是你的用户认证逻辑，验证用户名和密码
    code = request.json.get('code')
    # TODO 发送http请求到https://api.weixin.qq.com/sns/jscode2session，并且携带
    # appid, secret, js_code, grant_type
    print("config内容")
    print(config)
    response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
        'appid': config['mini']['appid'],
        'secret': config['mini']['appsecret'],
        'js_code': code,
        'grant_type': 'authorization_code'
    })
    session_key = response.json()['session_key']
    openid = response.json()['openid']
    if(response.json()['errcode'] is None):
        user = session.query(User).filter(User.openid == openid).first()
        if user is None:
            user = User(name="默认用户名", openid=openid)
            session.add(user)
            session.commit()
        pass
    if response.status_code == 200:
        # 认证成功，生成JWT并返回给客户端
        access_token = create_access_token(identity=username)
        return {'access_token': access_token}, 200
    else:
        return {'message': 'Invalid credentials'}, 401