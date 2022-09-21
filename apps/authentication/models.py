# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from apps import db, login_manager
from apps.authentication.util import hash_pass


class Crypto(db.Model):
    __tablename__ = "cryptos"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True)
    symbol = db.Column(db.String(64), unique=True)
    # cmc_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String(64), db.ForeignKey("users.username"))
    crypto_id = db.relationship("Alert", backref="cryptos")


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    low_threshold = db.Column(db.Integer, nullable=True)
    high_threshold = db.Column(db.Integer, nullable=True)
    symbol = db.Column(db.String(64), db.ForeignKey("cryptos.symbol"))
    user_id = db.Column(db.String(64), db.ForeignKey("users.id"))
    notification_id = db.relationship("Notification", backref="alerts")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    slack = db.Column(db.String(64), nullable=True)
    discord = db.Column(db.String(64), nullable=True)
    telegram = db.Column(db.String(64), nullable=True)
    alert_id = db.Column(db.String(64), db.ForeignKey("alerts.id"))
    # comments = db.relationship("Alerts", backref="notifications")
    # crypto_id = db.relationship("Notification", backref="cryptos")


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)

    crypto_id = db.relationship("Crypto", backref="users")

    # notification_id = db.relationship("Notification", backref="users")

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == "password":
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    return user if user else None
