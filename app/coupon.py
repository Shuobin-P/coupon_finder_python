from flask import Blueprint, request, jsonify
from sqlalchemy import and_
from datetime import datetime
from .models.coupon_finder_db_model import Coupon, GoodsDetailImage, User, CardPackageCoupon
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from . import coupon_finder_engine
import requests
from sqlalchemy.orm import sessionmaker

session = sessionmaker(bind = coupon_finder_engine)()
coupon_bp = Blueprint("coupon", __name__, url_prefix="/coupon")

# 请从coupon表中根据coupon的使用数量按照从多到少的顺序查询所有数据
# 并将查询结果转换为json格式
@jwt_required()
@coupon_bp.route('/getHotCoupons', methods=['GET'])
def getHotDrinkCoupons():
    page_num = int(request.args.get("pageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    now_time = datetime.now()
    category_id = request.args.get("categoryId", 2)
    query = session.query(Coupon).filter(
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
    # 关闭 Session
    session.close()    
    return {"data": coupons}

@jwt_required()
@coupon_bp.route('/getHotFoodCoupons', methods=['GET'])
def getHotFoodCoupons():
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

@jwt_required()
@coupon_bp.route("/getHotOtherCoupons", methods=['GET'])
def getHotOtherCoupons():
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
def getCouponInfo():
    # 从数据库查询到相关信息之后，需要处理一下数据格式，然后返回给前端
    query = session.query(Coupon).filter(
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
    session.close()
    imgs_list = session.query(GoodsDetailImage.img_url).filter(
        and_(
                GoodsDetailImage.coupon_id == request.args.get("id")
            )
    ).all()
    imgs_list_result = []
    for e in imgs_list:
        imgs_list_result.append(e[0])
    coupon_info[0].update({"images": imgs_list_result})
    session.close()
    return {"data": dict(coupon_info[0])}

@jwt_required()
@coupon_bp.route("/getCoupon", methods=['GET'])
def getCoupon():
    # TODO 领取优惠券会有超卖问题。
    # 原思路：如果优惠券数量>=1，该列的值减1。由于每条sql都是一个事务，然后根据事务的隔离级别
    # 不管是哪种都不会发生 脏写的问题，但是这里不是脏写问题。
    # 事务不是串行执行的。

    # 如果使用悲观锁实现，系统很安全，并发量小的时候，性能可能没有乐观锁好（但是这个影响不大吧），系统并发量大的时候，性能谁更好呢？
    # 但是使用乐观锁，在系统并发量不大的时候，性能会更好。但是在并发量大的时候，性能如何？
    coupon_id = request.args.get("couponId")
    verify_jwt_in_request()
    session.close()
    session.begin()
    open_id = get_jwt_identity()
    # 每种优惠券，每个用户只能领取一张
    card_package_id = session.query(User.card_package_id).filter(User.open_id == open_id).first()
    result = session.query(CardPackageCoupon).filter_by(
        card_package_id = card_package_id,
        coupon_id = coupon_id,
        status = 1
        ).first()
    if result is not None:
        return jsonify({"msg": "已经领取过了"}), 400

    coupon = session.query(Coupon).filter(Coupon.id == coupon_id).with_for_update().first()
    session.commit()
    if(coupon.remaining_quantity > 0):
        session.query(Coupon).filter(Coupon.id == coupon_id).update({
            "collected_quantity": coupon.collected_quantity + 1,
            "remaining_quantity": coupon.remaining_quantity - 1
            })
        
        # TODO 根据请求携带的jwt中的open_id，将优惠券领取信息插入到数据库中
        session.query(CardPackageCoupon).add_entity(CardPackageCoupon(card_package_id, coupon_id, 1))
        session.commit()

    pass

@coupon_bp.route("/findCoupon", methods=['GET'])
def findCoupon():
    
    pass
