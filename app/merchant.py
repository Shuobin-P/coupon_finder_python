import yaml,os, shutil
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt, create_access_token
from . import utils
from .models.coupon_finder_db_model import UserRole, Coupon, GoodsDetailImage

merchant_bp = Blueprint("merchant", __name__, url_prefix="/merchant")
with open('app\config.yml') as f:
    config = yaml.safe_load(f)

@jwt_required()
@merchant_bp.route('/verify', methods=['GET'])
def verify():
    key = request.args.get("key", 0)
    if int(key) == int(config['mini']['merchantSecret']):
        open_id = get_jwt_identity()
        g.db_session.add(UserRole(user_id=utils.get_user_id(open_id), role_id=1))
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
    if not os.path.exists('app/static/img/' + open_id):
        os.mkdir('app/static/img/' + open_id)
    request.files['file'].save('app/static/img/' + open_id +'/'+ file_name+ '.jpg')
    return jsonify({
        "data": file_name + '.jpg'
    })

@jwt_required()
@merchant_bp.route('/commitNewCouponInfo', methods=['POST'])
def commit_new_coupon_info():
    verify_jwt_in_request()
    # TODO 由于需要上传图片到七牛云，如果网络比较慢，就会造成服务器响应速度慢，用户体验不好，可以使用
    # 异步进行处理
    open_id = get_jwt_identity()
    coupon_info = request.get_json()
    # 上传产品图片
    if len(coupon_info['product_img']) != 0:
        utils.upload_file('app/static/img/' + open_id, coupon_info['product_img'])
    t = utils.get_current_ts()
    if t < coupon_info['start_date']:
        status = 0
    elif t < coupon_info['expire_date']:
        status = 1
    elif t >= coupon_info['expire_date']:
        status = 2
    category_id = utils.get_coupon_category_id(coupon_info['category'])
    merchant_id = utils.get_user_id(open_id)
    product_img = "http://" +config['qiniu']['path']+'/'+ coupon_info['product_img']
    cp = Coupon(
            coupon_info['title'], status, product_img, 
            coupon_info['description'], coupon_info['total_quantity'], 0,
            0, coupon_info['total_quantity'], utils.format_ts(coupon_info['start_date']), 
            utils.format_ts(coupon_info['expire_date']), category_id, coupon_info['original_price'], 
            coupon_info['present_price'], merchant_id, utils.format_ts(utils.get_current_ts())
        )
    g.db_session.add(cp)
    g.db_session.commit()
    # 上传产品详细信息图片
    for e in coupon_info['product_detail_img']:
        utils.upload_file('app/static/img/' + open_id, e)
        g.db_session.add(GoodsDetailImage(coupon_id = cp.id, img_url = "http://" +config['qiniu']['path']+'/'+ e))
    g.db_session.commit()
    # 如果有图片上传到了服务器，但是最后提交到七牛云的时候，这些图片并没有被使用，删除这些图片
    shutil.rmtree('app/static/img/' + open_id)
    return jsonify({
        "data": {
            "code": 1
        }
    })

@jwt_required()
@merchant_bp.route('/getUpcomingCoupons', methods=['GET'])
def get_upcoming_coupons():
    verify_jwt_in_request()
    open_id = get_jwt_identity()
    merchant_id = utils.get_user_id(open_id)
    current_date = utils.format_ts(utils.get_current_ts())
    coupons = g.db_session.query(Coupon).filter(
        Coupon.merchant_id == merchant_id, 
        Coupon.start_date > current_date,
        ).all()
    result = [{k: v for k,v in coupon.__dict__.items() if k != '_sa_instance_state'} for coupon in coupons]
    return jsonify({
        "data": result
    })
    

@jwt_required()
@merchant_bp.route('/getReleasedValidCoupons', methods=['GET'])
def get_released_valid_coupons():
    verify_jwt_in_request()
    open_id = get_jwt_identity()
    merchant_id = utils.get_user_id(open_id)
    current_date = utils.format_ts(utils.get_current_ts())
    coupons = g.db_session.query(Coupon).filter(
        Coupon.merchant_id == merchant_id, 
        Coupon.start_date <= current_date,
        Coupon.expire_date > current_date
        ).all()
    result = [{k: v for k,v in coupon.__dict__.items() if k != '_sa_instance_state'} for coupon in coupons]
    return jsonify({
        "data": result
    })


@jwt_required()
@merchant_bp.route('/getExpiredCoupon', methods=['GET'])
def get_expired_coupon():
    verify_jwt_in_request()
    # 获得该用户已发布的过期优惠券，即当前时间大于优惠券过期时间
    open_id = get_jwt_identity()
    merchant_id = utils.get_user_id(open_id)
    coupons = g.db_session.query(Coupon).filter(
        Coupon.merchant_id == merchant_id, Coupon.expire_date <= utils.format_ts(utils.get_current_ts())
        ).all()
    result = [{k: v for k,v in coupon.__dict__.items() if k != '_sa_instance_state'} for coupon in coupons]
    return jsonify({
        "data": result
    })
