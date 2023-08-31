from flask import Blueprint, request, jsonify
from . import redis_pool,redis
search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route('/updateKeywordsAppearingTimes', methods=['GET'])
def update_redis_keywords_appearing_times():
    keyword = request.args.get("keywords")
    redis_conn = redis.Redis(connection_pool=redis_pool)
    redis_conn.zincrby("coupon_finder:search_keywords_zset", 1, keyword)
    return jsonify({"msg": "更新成功"}), 200

@search_bp.route('/getTopNHotSearchKeywords', methods=['GET'])
def get_top_n_hot_search_keywords():
    top_n = request.args.get("top_n")
    redis_conn = redis.Redis(connection_pool=redis_pool)
    # 获取按照值从大到小排序的键
    sorted_keys = redis_conn.zrevrange('coupon_finder:search_keywords_zset', 0, top_n)
    keys = [key.decode('utf-8') for key in sorted_keys]
    return jsonify({"data": keys})