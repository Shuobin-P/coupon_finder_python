import os
import redis
from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import JWTManager
def create_app(test_config=None):
    # create and configure the app
        global coupon_finder_engine
        global redis
        app = Flask(__name__, instance_relative_config=True)
        app.config.from_mapping(
            SECRET_KEY='dev',
        )
        if test_config is None:
            # load the instance config, if it exists, when not testing
            app.config.from_pyfile('config.py', silent=True)
        else:
            # load the test config if passed in
            app.config.from_mapping(test_config)
        coupon_finder_engine = create_engine("mysql://root:123456@localhost/coupon_finder?charset=utf8",pool_size=10, max_overflow=20)
        # ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass
        app.config['JSON_AS_ASCII'] = False
        app.config['JWT_SECRET_KEY'] = '123456'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
        JWTManager(app)
        from . import coupon, login, search, wallet, merchant
        app.register_blueprint(login.login_bp)
        app.register_blueprint(coupon.coupon_bp)
        app.register_blueprint(search.search_bp)
        app.register_blueprint(wallet.wallet_bp)
        app.register_blueprint(merchant.merchant_bp)

        @app.before_request
        def before_request():
            get_redis()      
            get_db_session()
        return app

def get_db_session():
    if 'db_session' not in g:
        # 创建数据库连接
        g.db_session = sessionmaker(bind = coupon_finder_engine)()
    return g.db_session
     
def get_redis():
    if 'redis_client' not in g:
        # 创建 Redis 客户端连接
        g.redis_client = redis.StrictRedis(host='localhost', port=6379, db=2, password='123456')
    return g.redis_client