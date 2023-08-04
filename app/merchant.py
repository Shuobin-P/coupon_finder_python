import yaml,os,time
from sqlalchemy.orm import sessionmaker
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt, create_access_token
from . import coupon_finder_engine, utils
from .models.coupon_finder_db_model import UserRole, Coupon

session = sessionmaker(bind = coupon_finder_engine)()
merchant_bp = Blueprint("merchant", __name__, url_prefix="/merchant")
with open('app\config.yml') as f:
    config = yaml.safe_load(f)

@jwt_required()
@merchant_bp.route('/verify', methods=['GET'])
def verify():
    verify_jwt_in_request()
    key = request.args.get("key", 0)
    if int(key) == int(config['mini']['merchantSecret']):
        # TODO 在jwt中加入isMerchant为true
        # 并在user_role表中加入一条记录
        open_id = get_jwt_identity()
        session.add(UserRole(user_id=utils.get_user_id(open_id), role_id=1))
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
    open_id = get_jwt_identity()
    coupon_info = request.get_json()
    # 上传产品图片
    if len(coupon_info['product_img']) != 0:
        utils.upload_file('app/static/img/' + open_id, coupon_info['product_img'])
    # 上传产品详细信息
    for e in coupon_info['product_detail_img']:
        utils.upload_file('app/static/img/' + open_id, e)
    # TODO url保存到数据库
    t = int(time.time() * 1000)
    if t < coupon_info['start_date']:
        status = 0
    elif t < coupon_info['expire_date']:
        status = 1
    elif t >= coupon_info['expire_date']:
        status = 2
    category_id = utils.get_coupon_category_id(coupon_info['category'])
    print("category_id: ", category_id)
    Coupon(
        coupon_info['title'], status, coupon_info['product_img'], 
        coupon_info['description'], coupon_info['total_quantity'], 0,
        0, coupon_info['total_quantity'], coupon_info['start_date'], 
        coupon_info['expire_date'], coupon_info['category_id'], coupon_info['original_price'], 
        coupon_info['present_price'], coupon_info['merchant_id'], coupon_info['release_ts'])
    # TODO 将产品详细图片保存到数据库
    # TODO 将本地产品图片和详细信息删除
    return jsonify({
        "data": {
            "code": 1
        }
    })