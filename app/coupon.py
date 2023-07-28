from flask import Blueprint, request, jsonify
from sqlalchemy import and_
from datetime import datetime
import json
from .models.coupon_finder_db_model import Coupon, GoodsDetailImage

from . import coupon_finder_engine
import requests
from sqlalchemy.orm import sessionmaker

session = sessionmaker(bind = coupon_finder_engine)()
coupon_bp = Blueprint("coupon", __name__, url_prefix="/coupon")

# 请从coupon表中根据coupon的使用数量按照从多到少的顺序查询所有数据
# 并将查询结果转换为json格式
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

@coupon_bp.route("/getCoupon", methods=['GET'])
def getCoupon():
    pass
