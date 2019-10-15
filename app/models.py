from hashlib import md5
from time import time
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
    sample_input = db.Column(db.Text)
    sample_output = db.Column(db.Text)
    time_limit = db.Column(db.Integer())
    test_id = db.Column(db.Integer(), db.ForeignKey('test.id'))
    test_data = db.Column(db.Text)
    test = db.relationship('Test')
    template_id = db.Column(db.Integer(), db.ForeignKey('template.id'))
    template = db.relationship('Template')

    def set_test(self, test):
        self.test = test

    def set_template(self, template):
        self.template = template


class Test(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    code_id = db.Column(db.Integer(), db.ForeignKey('code.id'))
    code = db.relationship('Code')

    def set_code(self, code):
        self.code = code


class Template(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    code_id = db.Column(db.Integer(), db.ForeignKey('code.id'))
    code = db.relationship('Code')

    def set_code(self, code):
        self.code = code


class Solution(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    code_id = db.Column(db.Integer(), db.ForeignKey('code.id'))
    code = db.relationship('Code')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    user = db.relationship('User')
    is_default = db.Column(db.Boolean(), default=False)
    assignment_id = db.Column(db.Integer(), db.ForeignKey('assignment.id'))
    assignment = db.relationship('Assignment')
    is_submitted = db.Column(db.Boolean(), default=False)
    date_submitted = db.Column(db.DateTime, nullable=True)
    result = db.Column(db.Integer())
    result_text = db.Column(db.Text())

    def set_assignment(self, assignment):
        self.assignment = assignment

    def set_code(self, code):
        self.code = code

    def set_user(self, user):
        self.user = user


class Code(db.Model):
    id = db.Column(db.Integer(), primary_key=True, unique=True)
    path = db.Column(db.String(255))
