import threading
from . import coupon_finder_engine
from sqlalchemy.orm import sessionmaker
from .models.coupon_finder_db_model import User, Category, Coupon

# 创建 threadlocal 对象
thread_local_data = threading.local()

def get_db_session():
    if thread_local_data.db_session is None:
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