from . import coupon_finder_engine
from sqlalchemy.orm import sessionmaker
from .models.coupon_finder_db_model import  User

session = sessionmaker(bind = coupon_finder_engine)()

def get_card_package_id(open_id: str) -> int : 
    card_package_id = session.query(User.card_package_id).filter(User.open_id == open_id).first()
    session.close()
    return int(card_package_id[0])