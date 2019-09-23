from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app import db
from app.models import User
from app.administration import bp


@bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    return render_template('administration/create_user.html')


@bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    return render_template('administration/create_user.html')
