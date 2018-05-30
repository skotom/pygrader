from flask import render_template, flash, redirect, url_for, request, \
    current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User
from app.assignments.forms import AddAssignmentForm
from app.models import Course, Assignment
from app.assignments import bp


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
