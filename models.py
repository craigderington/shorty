from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
# Define application Bases


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(256), nullable=False)
    active = Column(Boolean, default=1)
    email = Column(String(120), unique=True, nullable=False)
    last_login = Column(DateTime)
    login_count = Column(Integer)
    fail_login_count = Column(Integer)
    created_on = Column(DateTime, default=datetime.now, nullable=True)
    changed_on = Column(DateTime, default=datetime.now, nullable=True)
    created_by_fk = Column(Integer)
    changed_by_fk = Column(Integer)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return int(self.id)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        if self.last_name and self.first_name:
            return "{} {}".format(
                self.first_name,
                self.last_name
            )


class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, onupdate=datetime.now)
    ip = Column(String(15), index=True)
    user_agent = Column(String(255))
    job_number = Column(Integer)
    client_id = Column(String(255))
    appended = Column(Boolean, default=False)
    open_hash = Column(String(255))
    campaign_hash = Column(String(255))
    send_hash = Column(String(255))
    num_visits = Column(Integer)
    last_visit = Column(DateTime)
    raw_data = Column(Text)
    processed = Column(Boolean, default=False)
    country_name = Column(String(255))
    city = Column(String(255))
    time_zone = Column(String(50))
    longitude = Column(String(50))
    latitude = Column(String(50))
    metro_code = Column(String(10))
    country_code = Column(String(2))
    country_code3 = Column(String(3))
    dma_code = Column(String(3))
    area_code = Column(String(3))
    postal_code = Column(String(5))
    region = Column(String(50))
    region_name = Column(String(255))
    traffic_type = Column(String(255))
    retry_counter = Column(Integer)
    last_retry = Column(DateTime)
    status = Column(String(10))
    locked = Column(Boolean, default=0)

    def __repr__(self):
        return "From {} on {} for {}".format(
            self.ip,
            self.created_date,
            self.campaign
        )

    def get_geoip_data(self):
        return "{} {} {} {} {}".format(
            self.country_code,
            self.city,
            self.region,
            self.postal_code,
            self.traffic_type
        )


class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    name = Column(String(500))
    full_url = Column(String(5000))
    short_url = Column(String(10), unique=True)
    full_hash = Column(String(64), unique=True)
    raw_request_headers = Column(Text)
    request_headers_hash = Column(String(255), unique=True)
    global_id = Column(String(36), unique=True)
    created_on_date = Column(DateTime, onupdate=datetime.now)
    modified_date = Column(DateTime, onupdate=datetime.now)
    clicks = Column(Integer)
    archived = Column(Boolean, default=False)
    url_last_checked_datetime = Column(DateTime)
    is_url_active = Column(Boolean, default=True)

    def __repr__(self):
        return "URL ID & Hash: {}/{}".format(str(self.id), self.short_url)

    def get_full_url(self):
        return "{}".format(self.full_url)
    
    def get_hash(self):
        return "{}".format(self.short_url)

    def is_active(self):
        return self.is_url_active
    
    def get_clicks(self):
        return int(self.clicks)
    
    def get_name(self):
        return "{}".format(str(self.name))
