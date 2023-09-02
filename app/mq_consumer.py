# -*- coding: UTF-8 -*-
import pika
import sys
import os,mq_utils,shutil, json, yaml
from models.coupon_finder_db_model import Coupon, GoodsDetailImage

with open('./config.yml') as f:
    config = yaml.safe_load(f)

def main():
    credentials = pika.PlainCredentials(config['rabbitmq']['username'], str(config['rabbitmq']['password']))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=config['rabbitmq']['linuxServer'], credentials=credentials))
    dbsession = mq_utils.get_db_session()
    channel = connection.channel()

    channel.queue_declare(queue='hello')
    
    def commit_new_coupon_info(coupon_info):
        open_id = coupon_info['open_id']
        if len(coupon_info['product_img']) != 0:
            mq_utils.upload_file('../static/img/' + open_id, coupon_info['product_img'])
        t = mq_utils.get_current_ts()
        if t < coupon_info['start_date']:
            status = 0
        elif t < coupon_info['expire_date']:
            status = 1
        elif t >= coupon_info['expire_date']:
            status = 2
        category_id = mq_utils.get_coupon_category_id(coupon_info['category'])
        merchant_id = mq_utils.get_user_id(open_id)
        product_img = "http://" +config['qiniu']['path']+'/'+ coupon_info['product_img']
        cp = Coupon(
                coupon_info['title'], status, product_img, 
                coupon_info['description'], coupon_info['total_quantity'], 0,
                0, coupon_info['total_quantity'], mq_utils.format_ts(coupon_info['start_date']), 
                mq_utils.format_ts(coupon_info['expire_date']), category_id, coupon_info['original_price'], 
                coupon_info['present_price'], merchant_id, mq_utils.format_ts(mq_utils.get_current_ts())
            )
        dbsession.add(cp)
        dbsession.commit()
        for e in coupon_info['product_detail_img']:
            mq_utils.upload_file('./static/img/' + open_id, e)
        dbsession.add(GoodsDetailImage(coupon_id = cp.id, img_url = "http://" +config['qiniu']['path']+'/'+ e))
        dbsession.commit()
        # 如果有图片上传到了服务器，但是最后提交到七牛云的时候，这些图片并没有被使用，删除这些图片
        shutil.rmtree('./static/img/' + open_id)
        mq_utils.close_session()

    def callback(ch, method, properties, body):
        body_str = body.decode('utf-8')
        body_dict = json.loads(body_str)
        print("body_dict的内容: ",body_dict)
        if body_dict['name'] == "commitNewCouponInfo":
            commit_new_coupon_info(body_dict['data'])
            ch.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_consume(queue='hello', on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)