import yaml
import uuid
from . import coupon_finder_engine
from sqlalchemy.orm import sessionmaker
from .models.coupon_finder_db_model import  User, Category
from qiniu import Auth, put_file, etag

with open('app\config.yml') as f:
    config = yaml.safe_load(f)

session = sessionmaker(bind = coupon_finder_engine)()

def get_coupon_category_id(keyword: str) -> int:
    card_package_id = int(session.query(Category).filter(Category.name == keyword).first()[0])
    return card_package_id

def get_card_package_id(open_id: str) -> int : 
    card_package_id = session.query(User.card_package_id).filter(User.open_id == open_id).first()
    return int(card_package_id[0])

def get_user_id(open_id: str) -> int:
    user_id = session.query(User.id).filter(User.open_id == open_id).first()
    return int(user_id[0])

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