import yaml,os,time
from sqlalchemy.orm import sessionmaker
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt, create_access_token
from . import coupon_finder_engine, utils
from .models.coupon_finder_db_model import UserRole, Coupon, GoodsDetailImage

session = sessionmaker(bind = coupon_finder_engine)()
merchant_bp = Blueprint("merchant", __name__, url_prefix="/merchant")
with open('app\config.yml') as f:
    config = yaml.safe_load(f)

@jwt_required()
@merchant_bp.route('/verify', methods=['GET'])
def verify():
    key = request.args.get("key", 0)
    if int(key) == int(config['mini']['merchantSecret']):
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
    # 上传产品详细信息图片
    for e in coupon_info['product_detail_img']:
        utils.upload_file('app/static/img/' + open_id, e)
    t = utils.get_current_ts()
    if t < coupon_info['start_date']:
        status = 0
    elif t < coupon_info['expire_date']:
        status = 1
    elif t >= coupon_info['expire_date']:
        status = 2
    category_id = utils.get_coupon_category_id(coupon_info['category'])
    merchant_id = utils.get_user_id(open_id)
    product_img = "http://" +config['qiniu']['path']+ coupon_info['product_img']
    utils.upload_file('app/static/img/' + open_id, coupon_info['product_img'])
    os.remove('app/static/img/' + open_id +'/'+ coupon_info['product_img'])
    cp = Coupon(
            coupon_info['title'], status, product_img, 
            coupon_info['description'], coupon_info['total_quantity'], 0,
            0, coupon_info['total_quantity'], utils.format_ts(coupon_info['start_date']), 
            utils.format_ts(coupon_info['expire_date']), category_id, coupon_info['original_price'], 
            coupon_info['present_price'], merchant_id, utils.format_ts(utils.get_current_ts())
        )
    session.add(cp)
    session.commit()
    # 将产品详细图片上传到七牛云，并把url保存到数据库
    # 删除本地缓存的照片
    for e in coupon_info['product_detail_img']:
        utils.upload_file('app/static/img/' + open_id, e)
        os.remove('app/static/img/' + open_id +'/'+ e)
        session.add(GoodsDetailImage(coupon_id = cp.id, img_url = "http://" +config['qiniu']['path']+'/'+ e))
    session.commit()
    # TODO 如果有图片上传到了服务器，但是最后提交到七牛云的时候，这些图片并没有被使用，那么如何删除这些图片？
    return jsonify({
        "data": {
            "code": 1
        }
    })