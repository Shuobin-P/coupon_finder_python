from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, TIMESTAMP
Base = declarative_base()
class Coupon(Base):
    __tablename__ = "coupon"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(20), unique=True, nullable=False)
    status = Column(String(255))
    picture_url = Column(String(500))
    description = Column(String(255))
    total_quantity = Column(Integer, nullable=False)
    used_quantity = Column(Integer, nullable=False)
    collected_quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)
    start_date = Column(DateTime)
    expire_date = Column(DateTime)
    category_id = Column(Integer)
    original_price = Column(DECIMAL)
    present_price = Column(DECIMAL)
    merchant_id = Column(Integer)
    release_ts = Column(TIMESTAMP)


    
    def __init__(self, title, status, picture_url, description, total_quantity, used_quantity, collected_quantity, remaining_quantity, start_date, expire_date, category_id, original_price, present_price, merchant_id, release_ts):
        self.title = title
        self.status =  status
        self.picture_url = picture_url
        self.description = description
        self.total_quantity = total_quantity
        self.used_quantity = used_quantity
        self.collected_quantity = collected_quantity
        self.remaining_quantity = remaining_quantity
        self.start_date = start_date
        self.expire_date = expire_date
        self.category_id = category_id
        self.original_price = original_price
        self.present_price = present_price
        self.merchant_id = merchant_id
        self.release_ts = release_ts

class GoodsDetailImage(Base):
    __tablename__ = "goods_detail_image"
    
    id = Column(Integer, primary_key=True)
    coupon_id = Column(Integer, nullable=False)
    img_url = Column(String(500), nullable=False)
    
    def __init__(self, coupon_id, img_url):
        self.coupon_id = coupon_id
        self.img_url = img_url

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    open_id = Column(String, nullable=False)
    card_package_id = Column(Integer, nullable=False)
    
    def __init__(self, name, open_id, card_package_id):
        self.name = name
        self.open_id = open_id
        self.card_package_id = card_package_id

class UserRole(Base):
    __tablename__ = "user_role"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
    
    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id

class CardPackageCoupon(Base):
    __tablename__ = "card_package_coupon"

    id = Column(Integer, primary_key=True)
    card_package_id = Column(Integer, nullable=False)
    coupon_id = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    
    def __init__(self, card_package_id, coupon_id, status):
        self.card_package_id = card_package_id
        self.coupon_id = coupon_id
        self.status = status