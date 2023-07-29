import os
from flask import Flask
from sqlalchemy import create_engine
from flask_jwt_extended import JWTManager

def create_app(test_config=None):
    # create and configure the app
        global coupon_finder_engine
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
        coupon_finder_engine = create_engine("mysql://root:123456@localhost/coupon_finder?charset=utf8")
        # ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass
        app.config['JSON_AS_ASCII'] = False
        app.config['JWT_SECRET_KEY'] = '123456'
        jwt = JWTManager(app)
        from . import coupon, login        
        app.register_blueprint(login.login_bp)
        app.register_blueprint(coupon.coupon_bp)

        
        return app