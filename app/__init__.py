import os
import pika
import redis
import yaml
from flask import Flask, g
from sqlalchemy import create_engine
from flask_jwt_extended import JWTManager

with open('app\config.yml') as f:
    config = yaml.safe_load(f)

def create_app(test_config=None):
        # create and configure the app
        global coupon_finder_engine
        global redis
        global redis_pool
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
        redis_pool = redis.ConnectionPool(
            host=config['redis']['winServer'], port=config['redis']['port'], db=2, max_connections=10,password=config['redis']['password']
        )
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
            # FIXME 这样处理毫无必要，不会在性能上有所提升，在创建数据库连接池之后，不需要手动进行管理。
            get_mq_connection()

        @app.after_request
        def after_request(response):
            # 在响应发送前设置响应头
            response.headers['X-Custom-Header'] = 'Hello'
            return response
        
        @app.teardown_request
        def after_requets(request):
            close_mq_connection()
        return app
     
def get_mq_connection():
    if 'mq_connection' not in g:
        credentials = pika.PlainCredentials(config['rabbitmq']['username'], str(config['rabbitmq']['password']))
        g.mq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',credentials=credentials))
    return g.mq_connection

def close_mq_connection():
    mq_connection = getattr(g, 'mq_connection', None)
    if mq_connection:
        mq_connection.close()
        g.mq_connection = None