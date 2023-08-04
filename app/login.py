import yaml,requests, time
from flask import request, Blueprint
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import create_access_token
from .models.coupon_finder_db_model import User, UserRole
from . import coupon_finder_engine

login_bp = Blueprint("login", __name__, url_prefix="/login")
session = sessionmaker(bind = coupon_finder_engine)()
with open('app\config.yml') as f:
    config = yaml.safe_load(f)

@login_bp.route('', methods=['POST'])
def login():
    # 假设这里是你的用户认证逻辑，验证用户名和密码
    code = request.json.get('code')
    # 发送http请求到https://api.weixin.qq.com/sns/jscode2session，并且携带
    # appid, secret, js_code, grant_type
    response = requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
        'appid': config['mini']['appid'],
        'secret': config['mini']['appsecret'],
        'js_code': code,
        'grant_type': 'authorization_code'
    }, proxies ={ "http": None, "https": None})
    session_key = response.json()['session_key']
    openid = response.json()['openid']
    if(response.json().get('errcode') is None):
        k_v = {}
        k_v.update({"username": openid, "session_key": session_key, "created": int(time.time()*1000)})
        user_id = -1
        user = session.query(User).filter(User.open_id == openid).first()
        if user is None:
            user = User(name="默认用户名", open_id=openid)
            session.add(user)
            session.commit()
            user_id = int(session.query(User.id).filter(User.openid == openid).first()[0])
            session.query(User).filter(User.id == user_id).update({User.card_package_id: user_id})
            session.commit()
        else:
            user_id = int(user.id)
        role_id = int(session.query(UserRole.role_id).filter(UserRole.user_id == user_id).first()[0])
        if role_id == 1:
            k_v.update({"isMerchant": True})
    if response.status_code == 200:
        # 认证成功，生成JWT并返回给客户端
        access_token = create_access_token(identity=openid, additional_claims=k_v)
        
        return {
            'data': 
                {
                    'tokenHead': 'Bearer ',
                    'token': access_token
                    }
                }
    else:
        return {'message': 'Invalid credentials'}, 401