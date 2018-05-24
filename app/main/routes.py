import os
import io
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm
from app.models import User
from app.main import bp
from werkzeug.utils import secure_filename


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title='Home')


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@bp.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    code = ''
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], current_user.username)

            if not os.path.exists(user_path):
                os.makedirs(user_path)

            path = os.path.join(user_path, filename)

            file.save(path)
            code = read_file(path)
            flash('Successfully saved file')
    return render_template('editor.html', code=code)


@bp.route('/editor/<filename>', methods=['GET', 'POST'])
@login_required
def edit_file():
    return render_template('editor.html')


def read_file(path):
    contents = ""
    with io.open(path, 'r', encoding='utf8') as f:
        contents = f.read()
    return contents


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower(
           ) in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
