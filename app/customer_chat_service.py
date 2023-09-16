from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request
customer_chat_service_bp = Blueprint("customer_chat_service", __name__, url_prefix="/customer_chat_service")

@jwt_required()
@customer_chat_service_bp.route('/get_cs_with_customer_chat_history', methods=['GET'])
def get_cs_with_customer_chat_history():
    """
        获得客服与消费者在某店铺的聊天记录。

        Args:
            shopID: 
            pageNum:
            pageSize:
        Returns:
            list: 
                item: 消费者昵称，头像，最新的聊天内容，发送的时间，未读消息数。（并且需要根据发送的时间从晚到早进行排序）

    """
    verify_jwt_in_request()
    shop_id = request.args.get("shopID", 0)
    page_num = int(request.args.get("pageNum", 1))
    page_size = int(request.args.get("pageSize", 10))
    # 过滤条件 WHERE shop_id = shop_id
    # 如果拿到10条与不同消费者的聊天信息？
    '''
    SELECT consumer_id, msg, sending_ts, 
        COUNT(*) OVER(PARTITION BY consumer_id ORDER BY sending_ts) as unread_msgs
    FROM chat_history
    WHERE shop_id = 1
    '''
    pass