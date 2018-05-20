import base64
from datetime import datetime, timedelta
from hashlib import md5
from time import time
import os
from flask import current_app
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

enrollments = db.Table(
    'enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id'))
    role = db.relationship('Role')
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    auto_save_code = db.Column(db.Boolean)
    courses = db.relationship(
        'Course', secondary=enrollments,
        primaryjoin=(enrollments.c.user_id == id),
        backref=db.backref('enrollments', lazy='dynamic'), lazy='dynamic')

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def enroll(self, course):
        if not self.is_enrolled(course):
            self.courses.append(course)

    def withdraw(self, course):
        if self.is_enrolled(course):
            self.courses.remove(course)

    def is_enrolled(self, course):
        return self.courses.filter(
            enrollments.c.course_id == course.id).count() > 0


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    name = db.Column(db.String(50), unique=True)


class Course(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    title = db.Column(db.String(100), unique=True)
    creator_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    creator = db.relationship('User')

    users = db.relationship(
        'User', secondary=enrollments,
        primaryjoin=(enrollments.c.course_id == id),
        backref=db.backref('enrollments', lazy='dynamic'), lazy='dynamic')


class Assignment(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    course_id = db.Column(db.Integer(), db.ForeignKey('course.id'))
    course = db.relationship('Course')
    title = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    test_id = db.Column(db.Integer(), db.ForeignKey('test.id'))
    test = db.relationship('Test')


class Test(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    code_id = db.Column(db.Integer(), db.ForeignKey('code.id'))
    code = db.relationship('Code')


class Solution(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    user = db.relationship('User')
    code_id = db.Column(db.Integer(), db.ForeignKey('code.id'))
    code = db.relationship('Code')
    is_completed = db.Column(db.Boolean)


class Code(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    path = db.column(db.String)
