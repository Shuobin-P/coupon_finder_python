from . import utils,coupon_finder_engine
from flask import Blueprint, request, jsonify, g
from sqlalchemy import and_,text
from datetime import datetime
from .models.coupon_finder_db_model import Coupon, GoodsDetailImage, User, CardPackageCoupon
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import requests
import time

coupon_bp = Blueprint("coupon", __name__, url_prefix="/coupon")

# 请从coupon表中根据coupon的使用数量按照从多到少的顺序查询所有数据
# 并将查询结果转换为json格式
@coupon_bp.route('/getHotCoupons', methods=['GET'])
def get_hot_drink_coupons():
    page_num = int(request.args.get("pageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    now_time = datetime.now()
    category_id = request.args.get("categoryId", 2)
    query = utils.get_db_session().query(Coupon).filter(
        and_(
            Coupon.category_id == category_id,
            Coupon.remaining_quantity > 0,
            now_time >= Coupon.start_date, 
            now_time <= Coupon.expire_date
        )
    )
    query = query.order_by(Coupon.used_quantity.desc())

    # 查询数据
    offset = (page_num - 1) * page_size
    before = time.time()
    coupons = query.offset(offset).limit(page_size).all()
    after = time.time()
    coupons = [{key: value for key, value in coupon.__dict__.items() if key != '_sa_instance_state'} for coupon in coupons]
    return {"data": coupons,"time_cost": after - before}

@coupon_bp.route('/getHotFoodCoupons', methods=['GET'])
def get_hot_food_coupons():
    url = "http://localhost:5000/coupon/getHotCoupons"
    params = {}
    params['categoryId'] =  1
    params.update(request.args)
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return jsonify(data)  # 将返回的数据响应给前端
    except requests.exceptions.RequestException as e:
        return jsonify({'error': '请求转发失败', 'message': str(e)}), 500

@coupon_bp.route("/getHotOtherCoupons", methods=['GET'])
def get_hot_other_coupons():
    url = "http://localhost:5000/coupon/getHotCoupons"
    params = {}
    params['categoryId'] =  3
    params.update(request.args)
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return jsonify(data)  # 将返回的数据响应给前端
    except requests.exceptions.RequestException as e:
        return jsonify({'error': '请求转发失败', 'message': str(e)}), 500

#@jwt_required()
@coupon_bp.route("/getCouponInfo", methods=['GET'])
def get_coupon_info():
    # 从数据库查询到相关信息之后，需要处理一下数据格式，然后返回给前端
    #verify_jwt_in_request()
    query = utils.get_db_session().query(Coupon).filter(
        and_(
            Coupon.id == request.args.get("id")
        ))
    coupon_info = query.all()
    coupon_info = [
        {key: value for key, value in coupon.__dict__.items() 
         if key != '_sa_instance_state'} 
         for coupon in coupon_info
                    ]
    coupon_info[0].update({"start_date" : int(coupon_info[0].get("start_date").timestamp()) * 1000})
    coupon_info[0].update({"expire_date" : int(coupon_info[0].get("expire_date").timestamp()) * 1000})
    imgs_list = utils.get_db_session().query(GoodsDetailImage.img_url).filter(
        and_(
                GoodsDetailImage.coupon_id == request.args.get("id")
            )
    ).all()
    imgs_list_result = []
    for e in imgs_list:
        imgs_list_result.append(e[0])
    coupon_info[0].update({"images": imgs_list_result})
    return {"data": dict(coupon_info[0])}

@jwt_required()
@coupon_bp.route("/getCoupon", methods=['GET'])
def get_coupon():
    # 领取优惠券会有超卖问题。
    # 原思路：如果优惠券数量>=1，该列的值减1。由于每条sql都是一个事务，然后根据事务的隔离级别
    # 不管是哪种都不会发生 脏写的问题，但是这里不是脏写问题。
    # 事务不是串行执行的。
    verify_jwt_in_request()
    coupon_id = request.args.get("couponId")
    open_id = get_jwt_identity()
    # 每种优惠券，每个用户只能领取一张
    card_package_id = utils.get_db_session().query(User.card_package_id).filter(User.open_id == open_id).first()[0]
    print("卡包ID： ", card_package_id)
    result = utils.get_db_session().query(CardPackageCoupon).filter_by(
        card_package_id = card_package_id,
        coupon_id = coupon_id,
        status = 1
        ).first()
    if result is not None:
        return jsonify({"msg": "已经领取过了"}), 400
    utils.get_db_session().commit()
    # 我：我查询到优惠券的数量大于0，先给这个记录上锁，以防止出现并发访问，再减去优惠券的数量
    # 但是如果大多数情况下，不会出现并发访问，那增加锁，就会降低性能。如何处理出现并发访问的时候带来的问题呢？
    # 出现并发访问的问题，就是优惠券的数量与查询时不一致，因此，执行update的时候，判断语句需要加上优惠券的数量
    # 与查询时的数量是否一致，如果不一致，就不执行update语句。
    # coupon = g.db_session.query(Coupon).filter(Coupon.id == coupon_id).with_for_update().first()
    # if(coupon.remaining_quantity > 0):
    #     g.db_session.query(Coupon).filter(Coupon.id == coupon_id).update({
    #         "collected_quantity": coupon.collected_quantity + 1,
    #         "remaining_quantity": coupon.remaining_quantity - 1
    #         })
    #     # 领取优惠券，将优惠券放入用户的卡包中        
    #     g.db_session.query(CardPackageCoupon).add_entity(CardPackageCoupon(card_package_id, coupon_id, 1))
    #     g.db_session.commit()
    while(True):
        coupon = utils.get_db_session().query(Coupon).filter(Coupon.id == coupon_id).first()
        if(coupon.remaining_quantity > 0):
            update_cnt = utils.get_db_session().query(Coupon)\
                .filter(Coupon.id == coupon_id, Coupon.remaining_quantity == coupon.remaining_quantity)\
                .update({
                            "collected_quantity": coupon.collected_quantity + 1,
                            "remaining_quantity": coupon.remaining_quantity - 1
                        }) > 0
            utils.get_db_session().commit()
            if(update_cnt > 0):
                break
        else:
            return jsonify({"msg": "优惠券已经领完了"}), 400
    return jsonify({"msg": "领取成功"}), 200

@jwt_required()
@coupon_bp.route("/findCoupon", methods=['GET'])
def find_coupon():
    verify_jwt_in_request()
    query_keyword = str(request.args.get("queryInfo"))
    sql_query = text(f"SELECT * FROM coupon WHERE MATCH(title) AGAINST(\"{query_keyword}\")")
    # 执行查询
    before = time.time()
    result = coupon_finder_engine.connect().execute(sql_query)
    after = time.time()
    print("查询耗时： ", after - before)
    coupons = [{key: value for key, value in coupon.__dict__.items() if key != '_sa_instance_state'} for coupon in result]
    return jsonify({"data": coupons,"time_gap": after - before})

@coupon_bp.route("/generateQRCode", methods=['GET'])
def generate_qrcode():
    # content字段其实就是一个url，用户扫描该二维码的时候，实际上，就是访问这个url
    # 因此，本接口就是把content字段的内容，放入二维码中，然后把二维码返回给前端
    url = request.args.get("content")
    byte_array = utils.get_qrcode_byte_stream(url)
    return byte_array

@jwt_required()
@coupon_bp.route("/useCoupon", methods=['GET'])
def use_coupon():
    verify_jwt_in_request()
    wallet_id = request.args.get("wallet_id")
    coupon_id = request.args.get("coupon_id")
    open_id = get_jwt_identity()
    # 1. 判断优惠券是否该老板发布的
    # 2. 判断该优惠券是否在该卡包中，并且状态是未使用
    # 3. 判断该优惠券是否过期
    if utils.get_user_id(open_id) != utils.get_released_coupon_merchant_id(coupon_id):
        return jsonify({"msg": "该优惠券不是该老板发布的", "code": 2 }), 400
    query_result = utils.get_db_session().query(CardPackageCoupon.status, CardPackageCoupon.id).filter(
        CardPackageCoupon.card_package_id == wallet_id,
        CardPackageCoupon.coupon_id == coupon_id,
    ).first()
    status = query_result[0]
    card_package_coupon_id = query_result[1]
    if status == 2:
        return jsonify({"msg": "该优惠券已经使用过了", "code": 3 }), 400
    elif status == 3:
        return jsonify({"msg": "该优惠券已经过期了", "code": 4 }), 400
    expire_date = utils.get_db_session().query(Coupon.expire_date).filter(
        Coupon.id == coupon_id
    ).first()[0]
    expire_date = datetime.strptime(str(expire_date), "%Y-%m-%d %H:%M:%S")
    if expire_date < datetime.now():
        return jsonify({"msg": "该优惠券已经过期了", "code": 4 }), 400
    # 优惠券合法，消耗该优惠券
    # 在卡包 优惠券 表中，将该优惠券的状态改为已使用
    # 在coupon表中，将该优惠券的已使用数量加1，将剩余数量减1，领取数量-1
    utils.get_db_session().query(CardPackageCoupon).filter(
        CardPackageCoupon.id == card_package_coupon_id
    ).update({
        "status": 2,
        "used_ts": datetime.now().strftime("%Y-%m-%d")
    })
    utils.get_db_session().commit()
    utils.get_db_session().query(Coupon).filter(
        Coupon.id == coupon_id
    ).update({
        "used_quantity": Coupon.used_quantity + 1,
        "remaining_quantity": Coupon.remaining_quantity - 1,
        "collected_quantity": Coupon.collected_quantity - 1
    })
    return jsonify({"msg": "使用成功", "code": 1}), 200
