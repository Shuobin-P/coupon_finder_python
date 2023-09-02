import yaml,os,json
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt, create_access_token
from . import utils
from .models.coupon_finder_db_model import UserRole, Coupon

merchant_bp = Blueprint("merchant", __name__, url_prefix="/merchant")
with open('app/config.yml') as f:
    config = yaml.safe_load(f)

@jwt_required()
@merchant_bp.route('/verify', methods=['GET'])
def verify():
    key = request.args.get("key", 0)
    if int(key) == int(config['mini']['merchantSecret']):
        open_id = get_jwt_identity()
        utils.get_db_session().add(UserRole(user_id=utils.get_user_id(open_id), role_id=1))
        claims = get_jwt()
        claims.update({"isMerchant": True})
        access_token = create_access_token(identity=open_id, additional_claims=claims)
        return jsonify({"data": {
            "code": 1,
            "token": 'Bearer ' + access_token
        }})
    else:
        return jsonify({"data": {
            "code": 0
        }})
    
@jwt_required()
@merchant_bp.route('/upload', methods=['POST'])
def upload():
    verify_jwt_in_request()
    open_id = get_jwt_identity()
    # 先暂时存储到本地，因为用户可能重发，最后用户点击提交的时候，再把图片从本地上传到七牛云
    file_name = utils.generate_random_filename()
    if not os.path.exists('./static/img/' + open_id):
        os.makedirs('./static/img/' + open_id)
    request.files['file'].save('./static/img/' + open_id +'/'+ file_name+ '.jpg')
    return jsonify({
        "data": file_name + '.jpg'
    })

@jwt_required()
@merchant_bp.route('/commitNewCouponInfo', methods=['POST'])
def commit_new_coupon_info():
    verify_jwt_in_request()
    # 由于需要上传图片到七牛云，如果网络比较慢，就会造成服务器响应速度慢，用户体验不好，可以使用
    # 异步进行处理
    open_id = get_jwt_identity()
    channel = g.mq_connection.channel()
    channel.queue_declare(queue='hello')
    print("获得request的json数据", request.get_json())
    tmp = request.get_json()
    tmp.update({"open_id": open_id})
    print("tmp的类型：", type(tmp))
    print("处理之后呢？：", tmp)
    channel.basic_publish(
        exchange='',
        routing_key='hello',
        body = json.dumps({
            "name": "commitNewCouponInfo",
            "data": tmp
        }))
    return jsonify({
        "data": {
            "code": 1
        }
    })

@jwt_required()
@merchant_bp.route('/getUpcomingCoupons', methods=['GET'])
def get_upcoming_coupons():
    verify_jwt_in_request()
    page_num = int(request.args.get("upcomingCouponPageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    offset = (page_num - 1) * page_size
    open_id = get_jwt_identity()
    merchant_id = utils.get_user_id(open_id)
    current_date = utils.format_ts(utils.get_current_ts())
    query = utils.get_db_session().query(Coupon).filter(
        Coupon.merchant_id == merchant_id, 
        Coupon.start_date > current_date,
        )
    coupons = query.offset(offset).limit(page_size).all()
    result = [{k: v for k,v in coupon.__dict__.items() if k != '_sa_instance_state'} for coupon in coupons]
    return jsonify({
        "data": result
    })
    
@jwt_required()
@merchant_bp.route('/getReleasedValidCoupons', methods=['GET'])
def get_released_valid_coupons():
    verify_jwt_in_request()
    page_num = int(request.args.get("validCouponPageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    offset = (page_num - 1) * page_size
    open_id = get_jwt_identity()
    merchant_id = utils.get_user_id(open_id)
    current_date = utils.format_ts(utils.get_current_ts())
    query = utils.get_db_session().query(Coupon).filter(
        Coupon.merchant_id == merchant_id, 
        Coupon.start_date <= current_date,
        Coupon.expire_date > current_date
        )
    coupons = query.offset(offset).limit(page_size).all()
    result = [{k: v for k,v in coupon.__dict__.items() if k != '_sa_instance_state'} for coupon in coupons]
    return jsonify({
        "data": result
    })

@jwt_required()
@merchant_bp.route('/getExpiredCoupon', methods=['GET'])
def get_expired_coupon():
    verify_jwt_in_request()
    # 获得该用户已发布的过期优惠券，即当前时间大于优惠券过期时间
    page_num = int(request.args.get("expiredCouponPageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    offset = (page_num - 1) * page_size
    open_id = get_jwt_identity()
    merchant_id = utils.get_user_id(open_id)
    query = utils.get_db_session().query(Coupon).filter(
        Coupon.merchant_id == merchant_id, Coupon.expire_date <= utils.format_ts(utils.get_current_ts())
        )
    coupons = query.offset(offset).limit(page_size).all()
    result = [{k: v for k,v in coupon.__dict__.items() if k != '_sa_instance_state'} for coupon in coupons]
    return jsonify({
        "data": result
    })
