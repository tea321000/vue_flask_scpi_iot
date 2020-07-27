from datetime import datetime
from automation.sql import db
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from app import app


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.Unicode(20), nullable=False)
    birthday = db.Column(db.Date)
    password = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum('visitor', 'observer', 'manager',
                             'administrator'), nullable=False)
    permission = db.Column(db.Integer, nullable=False)
    feedbacks = db.relationship('Feedback', backref='user', lazy='dynamic')
    query_history = db.relationship(
        'QueryHistory', backref='user', lazy='dynamic')

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['USER_SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['USER_SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


class UserList(db.Model):
    __tablename__ = 'user_list'
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.Unicode(20), nullable=False)
    role = db.Column(db.Enum('visitor', 'observer',
                             'manager', 'administrator'), nullable=False)


class DeviceRegister(db.Model):
    __tablename__ = 'device_register'
    serial = db.Column(db.String(20), nullable=False, primary_key=True)
    mac = db.Column(db.String(128), nullable=False)
    user_agent = db.Column(db.Text, nullable=False)
    device_type = db.Column(db.JSON, nullable=False)
    device_set = db.Column(db.JSON, nullable=False)
    permission = db.Column(db.Integer, nullable=False)
    query_historys = db.relationship(
        'QueryHistory', backref='device', lazy='dynamic')
    # alive = db.relationship('DeviceAlive', uselist=False,
    #                         back_populates='device',  primaryjoin="DeviceRegister.mac==DeviceAlive.mac")
    alive = db.relationship('DeviceAlive', uselist=False,
                            back_populates='device')

    def hash_mac(self, mac):
        self.mac = pwd_context.encrypt(mac)

    def verify_mac(self, mac):
        return pwd_context.verify(mac, self.mac)

    def generate_auth_token(self, expiration=3600):
        s = Serializer(app.config['DEVICE_SECRET_KEY'], expires_in=expiration)
        return s.dumps({'serial': self.serial})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['DEVICE_SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        device = DeviceRegister.query.get(data['serial'])
        return device


class DeviceAlive(db.Model):
    __tablename__ = 'device_alive'
    serial = db.Column(db.String(20), db.ForeignKey(
        'device_register.serial'), primary_key=True)
    heartbeat_timestamp = db.Column(db.BigInteger, nullable=False)
    # permission = db.Column(db.Integer, db.ForeignKey(
    #     'device_register.permission'))
    # device = db.relationship('DeviceRegister',
    #                          back_populates='alive', primaryjoin="DeviceRegister.mac==DeviceAlive.mac")

    device = db.relationship('DeviceRegister', back_populates='alive')


class QueryHistory(db.Model):
    __tablename__ = 'query_history'
    id = db.Column(db.BigInteger, primary_key=True)
    device_serial = db.Column(
        db.String(20), db.ForeignKey('device_register.serial'))
    user_id = db.Column(db.String(10), db.ForeignKey('user.id'))
    query_timestamp = db.Column(db.BigInteger, nullable=False)
    command_content = db.Column(db.JSON)
    response = db.Column(db.JSON)


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.String(10), db.ForeignKey('user.id'))
    title = db.Column(db.Unicode(50), nullable=False)
    content = db.Column(db.UnicodeText)
