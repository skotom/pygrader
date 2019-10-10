from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app import db
from app.models import User, Role
from app.administration import bp
import sys


@bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role.name == 'admin':
        if request.method == 'GET':
            roles = Role.query.all()
            return render_template('administration/create_user.html', roles=roles)
        elif request.method == 'POST':
            role_id = request.form.get('roleId')
            username = request.form.get('username')
            email = request.form.get('email')
            users = User.query.all()
            if username in (user.username for user in users):
                return "ALREADY EXISTS"
            password = request.form.get('password')
            role = Role.query.filter_by(id=role_id).first()

            user = User(username=username, email=email,
                        role=role, auto_save_code=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            users = User.query.all()
            return render_template('administration/users.html', users=users)


@bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if current_user.role.name == 'admin':
        users = User.query.all()
    return render_template('administration/users.html', users=users)
