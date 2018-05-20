import os
import io
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm, AddCourseForm, AddAssignmentForm
from app.models import User, Course, Assignment
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


@bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    courses = Course.query.filter_by(creator_id=current_user.id)
    return render_template('courses.html', courses=courses)


@bp.route('/course/<int:id>', methods=['GET'])
@login_required
def course(id):
    course = Course.query.filter_by(id=id).first()
    assignments = Assignment.query.filter_by(course=course)
    return render_template('course.html', assignments=assignments, course=course)


@bp.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    form = AddCourseForm()
    if form.validate_on_submit():
        course = Course(title=form.title.data, creator_id=current_user.id)
        db.session.add(course)
        db.session.commit()
        flash('Successfully added new course.')
        return redirect(url_for('main.courses'))

    return render_template('add_course.html', title='Add course',
                           form=form)


@bp.route('/assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first()
    return render_template('assignment.html', assignment=assignment)


@bp.route('/course/<int:course_id>/add_assignment', methods=['GET', 'POST'])
@login_required
def add_assignment(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    form = AddAssignmentForm()
    if form.validate_on_submit():
        assignment = Assignment(title=form.title.data,
                                description=form.description.data,
                                course=course)

        db.session.add(assignment)
        db.session.commit()
        flash('Successfully added new assignment to {}'.format(course.title))
        return redirect(url_for('main.course', id=course.id))

    return render_template('add_assignment.html', title='Add assignment',
                           form=form)
