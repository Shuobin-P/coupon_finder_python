
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
customer_chat_service_bp = Blueprint("customer_chat_service", __name__, url_prefix="/customer_chat_service")

@jwt_required()
@customer_chat_service_bp.route('/get_cs_with_customer_chat_history', methods=['GET'])
def get_cs_with_customer_chat_history():
    """
        获得客服与消费者在某店铺的聊天记录
    """
    shop_id = request.args.get("shop_id", 0)
    pass