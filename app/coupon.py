from flask import Blueprint, request, jsonify, g
from sqlalchemy import and_
from datetime import datetime
from .models.coupon_finder_db_model import Coupon, GoodsDetailImage, User, CardPackageCoupon
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import requests


coupon_bp = Blueprint("coupon", __name__, url_prefix="/coupon")

# 请从coupon表中根据coupon的使用数量按照从多到少的顺序查询所有数据
# 并将查询结果转换为json格式
#@jwt_required()
@coupon_bp.route('/getHotCoupons', methods=['GET'])
def get_hot_drink_coupons():
    #verify_jwt_in_request()
    page_num = int(request.args.get("pageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    now_time = datetime.now()
    category_id = request.args.get("categoryId", 2)
    query = g.db_session.query(Coupon).filter(
        and_(
            Coupon.category_id == category_id,
            Coupon.total_quantity - Coupon.used_quantity - Coupon.collected_quantity > 0,
            now_time >= Coupon.start_date, 
            now_time <= Coupon.expire_date
        )
    )
    query = query.order_by(Coupon.used_quantity.desc())

    # 查询数据
    offset = (page_num - 1) * page_size
    coupons = query.offset(offset).limit(page_size).all()
    coupons = [{key: value for key, value in coupon.__dict__.items() if key != '_sa_instance_state'} for coupon in coupons]
    return {"data": coupons}

@jwt_required()
@coupon_bp.route('/getHotFoodCoupons', methods=['GET'])
def get_hot_food_coupons():
    verify_jwt_in_request()
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

#@jwt_required()
@coupon_bp.route("/getHotOtherCoupons", methods=['GET'])
def get_hot_other_coupons():
    # verify_jwt_in_request()
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

@jwt_required()
@coupon_bp.route("/getCouponInfo", methods=['GET'])
def get_coupon_info():
    # 从数据库查询到相关信息之后，需要处理一下数据格式，然后返回给前端
    verify_jwt_in_request()
    query = g.db_session.query(Coupon).filter(
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
    imgs_list = g.db_session.query(GoodsDetailImage.img_url).filter(
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
    card_package_id = g.db_session.query(User.card_package_id).filter(User.open_id == open_id).first()[0]
    print("卡包ID： ", card_package_id)
    result = g.db_session.query(CardPackageCoupon).filter_by(
        card_package_id = card_package_id,
        coupon_id = coupon_id,
        status = 1
        ).first()
    if result is not None:
        return jsonify({"msg": "已经领取过了"}), 400
    g.db_session.commit()
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
        coupon = g.db_session.query(Coupon).filter(Coupon.id == coupon_id).first()
        if(coupon.remaining_quantity > 0):
            update_cnt = g.db_session.query(Coupon)\
                .filter(Coupon.id == coupon_id, Coupon.remaining_quantity == coupon.remaining_quantity)\
                .update({
                            "collected_quantity": coupon.collected_quantity + 1,
                            "remaining_quantity": coupon.remaining_quantity - 1
                        }) > 0
            g.db_session.commit()
            if(update_cnt > 0):
                break
        else:
            return jsonify({"msg": "优惠券已经领完了"}), 400
    return jsonify({"msg": "领取成功"}), 200

@jwt_required()
@coupon_bp.route("/findCoupon", methods=['GET'])
def find_coupon():
    query_keyword = request.args.get("queryInfo")
    result = g.db_session.query(Coupon).filter(Coupon.title.like(f"%{query_keyword}%")).all()
    coupons = [{key: value for key, value in coupon.__dict__.items() if key != '_sa_instance_state'} for coupon in result]
    return jsonify({"data": coupons})
