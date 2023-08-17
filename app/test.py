import copy
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.coupon_finder_db_model import Coupon

with open('app/config.yml') as f:
    config = yaml.safe_load(f)

coupon_finder_engine = create_engine(
            "mysql://root:123456@localhost" + "/coupon_finder?charset=utf8",pool_size=10, max_overflow=20)

db_session = sessionmaker(bind=coupon_finder_engine)()
record = db_session.query(Coupon).filter(Coupon.id == 68).one()
db_session.close()
for index in range(1,200010):
    db_session.add(Coupon(
        title = record.title + str(index), 
        status = record.status,
        picture_url = record.picture_url,
        description = record.description,
        total_quantity = record.total_quantity,
        used_quantity = record.used_quantity,
        collected_quantity = record.collected_quantity,
        remaining_quantity = record.remaining_quantity,
        start_date = record.start_date,
        expire_date = record.expire_date,
        category_id = record.category_id,
        original_price = record.original_price,
        present_price = record.present_price,
        merchant_id = record.merchant_id,
        release_ts = record.release_ts
                          ))  # 添加新的记录
db_session.commit()  # 提交插入操作
db_session.close()