import yaml
import uuid
import time
import qrcode
from io import BytesIO
from flask import g
from app.models.coupon_finder_db_model import User, Category, Coupon
from sqlalchemy.orm import sessionmaker
from qiniu import Auth, put_file
from datetime import datetime
from . import coupon_finder_engine

with open('app/config.yml') as f:
    config = yaml.safe_load(f)

def get_coupon_category_id(keyword: str) -> int:
    card_package_id = get_db_session().query(Category).filter(Category.name == keyword).first().id
    return card_package_id

def get_card_package_id(open_id: str) -> int : 
    card_package_id = get_db_session().query(User.card_package_id).filter(User.open_id == open_id).first()
    return int(card_package_id[0])

def get_user_id(open_id: str) -> int:
    user_id = get_db_session().query(User.id).filter(User.open_id == open_id).first()
    return int(user_id[0])

def get_released_coupon_merchant_id(coupon_id: int) -> int:
    '''
        发布优惠券的商家的用户ID
    '''
    merchant_id = get_db_session().query(Coupon.merchant_id).filter(Coupon.id == int(coupon_id)).first()[0]
    return int(merchant_id)
    
def generate_random_filename():
    random_uuid = uuid.uuid4()
    return str(random_uuid)

def upload_file(file_dir_path: str, file_name: str):
    q = Auth(config['qiniu']['accessKey'], config['qiniu']['secretKey'])
    #要上传的空间
    bucket_name = config['qiniu']['bucketName']
    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, file_name, 3600)
    #要上传文件的本地路径
    put_file(token, file_name, file_dir_path + '/' + file_name, version='v2') 

def get_current_ts():
    '''
    获取当前时间戳 单位：毫秒
    '''
    return int(time.time() * 1000)

def format_ts(ts: int):
    '''
        将时间戳格式化为字符串%Y-%m-%d %H:%M:%S
    '''
    # 假设给定的时间戳为1691143122611
    timestamp = ts / 1000  # 将毫秒转换为秒
    datetime_obj = datetime.fromtimestamp(timestamp)

    # 格式化为字符串
    formatted_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

def get_qrcode_byte_stream(data) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # 将二维码图片以字节流的形式发送给前端
    img_byte_array = BytesIO()
    img.save(img_byte_array)
    img_byte_array.seek(0)
    return img_byte_array


def get_db_session():
    if 'db_session' not in g:
        g.db_session = sessionmaker(bind=coupon_finder_engine)()
    return g.db_session
