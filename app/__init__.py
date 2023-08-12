import os
import pika
import redis
import yaml
from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import JWTManager

with open('app/config.yml') as f:
    config = yaml.safe_load(f)

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
        coupon_finder_engine = create_engine(
            "mysql://root:123456@" + 
            str(config['mysql']['host']) + "/coupon_finder?charset=utf8",pool_size=10, max_overflow=20)
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
            get_mq_connection()
        @app.teardown_request
        def after_requets(request):
            close_session()
            close_mq_connection()
        return app

def get_db_session():
    if 'db_session' not in g:
        g.db_session = sessionmaker(bind=coupon_finder_engine)()
    return g.db_session

def close_session():
    db_session = getattr(g, 'db_session', None)
    if db_session:
        db_session.close()
        g.db_session = None
     
def get_redis():
    if 'redis_client' not in g:
        # 创建 Redis 客户端连接
        g.redis_client = redis.StrictRedis(
            host=config['redis']['host'],
            port=config['redis']['port'], 
            db=2, 
            password=config['redis']['password'])
    return g.redis_client

def get_mq_connection():
    if 'mq_connection' not in g:
        credentials = pika.PlainCredentials(config['rabbitmq']['username'], str(config['rabbitmq']['password']))
        g.mq_connection = pika.BlockingConnection(pika.ConnectionParameters(config['rabbitmq']['host'],credentials=credentials))
    return g.mq_connection

def close_mq_connection():
    mq_connection = getattr(g, 'mq_connection', None)
    if mq_connection:
        mq_connection.close()
        g.mq_connection = None