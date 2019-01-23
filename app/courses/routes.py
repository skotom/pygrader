from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app import db
from app.courses.forms import AddCourseForm
from app.models import Course, Assignment
from app.courses import bp


@bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    if(current_user.role.name == 'teacher'):
        courses = current_user.courses
    else:
        courses = Course.query.all()
    return render_template('courses/courses.html', courses=courses, title="My courses")


@bp.route('/course/<int:id>', methods=['GET'])
@login_required
def course(id):
    course = Course.query.filter_by(id=id).first()
    assignments = Assignment.query.filter_by(course=course)
    return render_template('courses/course.html', assignments=assignments, course=course)


@bp.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    form = AddCourseForm()
    if form.validate_on_submit():
        course = Course(title=form.title.data)
        db.session.add(course)
        db.session.commit()

        current_user.enroll(course)
        db.session.commit()
        flash('Successfully added new course.')
        return redirect(url_for('courses.course', id=course.id))

    return render_template('courses/add_course.html', title='Add course',
                           form=form)


@bp.route('/course/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(id):
    course = Course.query.filter_by(id=id).first()
    form = AddCourseForm()
    if form.validate_on_submit():
        course.title = form.title.data
        db.session.commit()
        flash('Successfully saved changes.')
        return redirect(url_for('courses.course', id=id))
    elif request.method == 'GET':
        form.title.data = course.title
    return render_template('courses/edit_course.html', title='Edit course',
                           form=form)

@bp.route('/course/<int:id>/users', methods=['GET', 'POST'])
@login_required
def users(id):
    course  = Course.query.filter_by(id=id).first()
    users = course.users

    if(current_user.role.name == 'teacher' and current_user in users):
        return render_template('courses/users.html', title='Course users', 
                            users=users, course=course)


