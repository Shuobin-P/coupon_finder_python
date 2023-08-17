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
record = db_session.query(Coupon).filter(Coupon.id == 41).one()
record_copy = copy.deepcopy(record)
record_copy.title = "全文索引测试数据"
db_session.close()
for index in range(63, 100):
    record_copy.id = index
    db_session.add(record_copy)
    db_session.commit()
db_session.close()