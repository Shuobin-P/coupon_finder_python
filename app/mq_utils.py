import threading
import time
import yaml
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.coupon_finder_db_model import User, Category
from qiniu import Auth, put_file

with open('app/config.yml') as f:
    config = yaml.safe_load(f)
# 创建 threadlocal 对象
thread_local_data = threading.local()
coupon_finder_engine = create_engine("mysql://root:123456@localhost/coupon_finder?charset=utf8",pool_size=10, max_overflow=20)

def get_db_session():
    db_session = getattr(thread_local_data, 'db_session', None)
    if db_session is None:
        thread_local_data.db_session = sessionmaker(bind=coupon_finder_engine)()
    return thread_local_data.db_session

def close_session():
    db_session = getattr(thread_local_data, 'db_session', None)
    if db_session:
        db_session.close()

def get_user_id(open_id: str) -> int:
    user_id = thread_local_data.db_session.query(User.id).filter(User.open_id == open_id).first()
    return int(user_id[0])

def get_coupon_category_id(keyword: str) -> int:
    card_package_id = thread_local_data.db_session.query(Category).filter(Category.name == keyword).first().id
    return card_package_id

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