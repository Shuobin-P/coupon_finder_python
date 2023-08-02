from sqlalchemy.orm import sessionmaker
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from . import coupon_finder_engine, utils
from .models.coupon_finder_db_model import CardPackageCoupon, Coupon, User

wallet_bp = Blueprint("wallet", __name__, url_prefix="/wallet")
session = sessionmaker(bind = coupon_finder_engine)()
@jwt_required()
@wallet_bp.route('/getAvailableCoupons', methods=['GET'])
def get_available_coupons():
    # 从jwt中提取出open_id
    # 根据open_id 从用户的wallet中取出领取的优惠券
    verify_jwt_in_request()
    open_id = get_jwt_identity()
    card_package_id = utils.get_card_package_id(open_id)
    ids = session.query(CardPackageCoupon.coupon_id).filter_by(card_package_id = card_package_id, status = 1).all()
    id_list = []
    for item in ids:
        id_list.append(item[0])
    result = session.query(Coupon).filter(Coupon.id.in_(id_list)).all()
    coupons = [{key: value for key, value in coupon.__dict__.items() if key != '_sa_instance_state'} for coupon in result]
    session.close()
    return jsonify({"data": coupons})

@jwt_required()
@wallet_bp.route('/getCouponUsedHistory', methods=['GET'])
def get_coupon_used_history():
    verify_jwt_in_request()
    open_id = get_jwt_identity()
    card_package_id = utils.get_card_package_id(open_id)
    sub_query = session.query(CardPackageCoupon)\
            .filter_by(card_package_id = card_package_id, status = 2)\
            .order_by(CardPackageCoupon.ts).subquery()
    result = session.query(
        Coupon.id,Coupon.title, Coupon.description, Coupon.picture_url, 
        Coupon.original_price, Coupon.present_price, sub_query.c.ts)\
        .outerjoin(Coupon, sub_query.c.coupon_id == Coupon.id)
    data = []
    for tp in result:
        tmp = {}
        tmp.update(
            {
                "title": tp[1],
                "description": tp[2],
                "picture_url": tp[3],
                "original_price": int(tp[4]),
                "present_price": int(tp[5]),
                "ts": tp[6]
             }
            )
        data.append(tmp)
    session.close()
    return jsonify({"data": data})
