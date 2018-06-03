import io
import os
from flask import render_template, flash, redirect, url_for, request, \
    current_app
from flask_login import login_required, current_user
from app import db
from app.assignments.forms import AddAssignmentForm
from app.models import Course, Assignment
from app.assignments import bp
from werkzeug.utils import secure_filename


@bp.route('/assignment/<int:id>', methods=['GET', 'POST'])
@login_required
def assignment(id):
    assignment = Assignment.query.filter_by(id=id).first()
    return render_template('assignments/assignment.html',
                           assignment=assignment)


@bp.route('/course/<int:course_id>/add_assignment', methods=['GET', 'POST'])
@login_required
def add_assignment(course_id):
    print(current_user.role.name)
    course = Course.query.filter_by(id=course_id).first_or_404()
    form = AddAssignmentForm()
    if form.validate_on_submit():
        assignment = Assignment(title=form.title.data,
                                description=form.description.data,
                                course=course)

        db.session.add(assignment)
        db.session.commit()
        flash('Successfully added new assignment to {}'.format(course.title))
        return redirect(url_for('courses.course', id=course.id))

    return render_template('assignments/add_assignment.html',
                           title='Add assignment',
                           form=form)


@bp.route('/assignment/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
    assignment = Assignment.query.filter_by(id=id).first()
    form = AddAssignmentForm()
    if form.validate_on_submit():
        assignment.title = form.title.data
        assignment.description = form.description.data
        db.session.commit()
        flash('Successfully saved changes')
        return redirect(url_for('assignments.assignment', id=id))
    elif request.method == 'GET':
        form.title.data = assignment.title
        form.description.data = assignment.description
    return render_template('assignments/edit_assignment.html',
                           title='Edit assignment',
                           form=form)


@bp.route('/editor/<int: assignment_id>', methods=['GET'])
@login_required
def editor(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id)
    course = assignment.course
    render_template('editor.html', assignment=assignment, course=course)


@bp.route('/save_file', methods=['GET', 'POST'])
@login_required
def save_code():
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
    return code


def read_file(path):
    contents = ""
    with io.open(path, 'r', encoding='utf8') as f:
        contents = f.read()
    return contents


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower(
           ) in current_app.config['ALLOWED_EXTENSIONS']
