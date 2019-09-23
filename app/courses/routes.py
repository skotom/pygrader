from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app import db
from app.models import Course, Assignment, User, Solution
from app.courses import bp


@bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    if(current_user.role.name in ['teacher', 'student']):
        courses = current_user.courses
    else:
        courses = Course.query.all()
    return render_template('courses/courses.html', courses=courses, title="Courses")


@bp.route('/course/<int:id>', methods=['GET'])
@login_required
def course(id):
    course = Course.query.filter_by(id=id).first()
    assignments = Assignment.query.filter_by(course=course)
    if current_user.role.name not in ['teacher', 'admin']:
        completed_assignments = []

        for assignment in assignments:
            default_solution = Solution.query.filter_by(
                assignment_id=assignment.id, is_default=True).first()

            if default_solution and assignment.test and assignment.template:
                completed_assignments.append(assignment)

        assignments = completed_assignments

    return render_template('courses/course.html', assignments=assignments, course=course)


@bp.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        course = Course(title=request.form['title'])
        db.session.add(course)
        db.session.commit()

        current_user.enroll(course)
        db.session.commit()
        flash('Successfully added new course.')
        return redirect(url_for('courses.course', id=course.id))

    return render_template('courses/add_course.html', title='Add course',)


@bp.route('/course/<int:id>/edit', methods=['GET', 'POST', 'PUT'])
@login_required
def edit_course(id):
    course = Course.query.filter_by(id=id).first()

    if request.method == 'POST':
        course.title = request.form['title']
        db.session.commit()
        flash('Successfully saved changes.')
        return redirect(url_for('courses.course', id=id))

    return render_template('courses/edit_course.html', title='Edit course', course=course)


@bp.route('/course/<int:id>/users', methods=['GET', 'POST'])
@login_required
def users(id):
    course = Course.query.filter_by(id=id).first()
    users = course.users

    if(current_user.role.name == 'teacher' and current_user in users) or current_user.role.name == 'admin':
        return render_template('courses/users.html', title='Course users',
                               users=users, course=course)


@bp.route('/course/<int:id>/enrolling', methods=['GET', 'POST'])
@login_required
def enrolling(id):
    course = Course.query.filter_by(id=id).first()
    enrolled_users = course.users
    all_users = db.session.query(User).all()  # TODO dont put admin here

    not_enrolled_users = [
        user for user in all_users if user not in enrolled_users]

    if(current_user.role.name == 'teacher' and current_user in enrolled_users) or current_user.role.name == 'admin':
        return render_template('courses/enrolling.html', title='Enroll users',
                               users=not_enrolled_users, course=course)
    # Handle unauthorized


@bp.route('/course/<int:id>/enroll/<int:user_id>', methods=['GET', 'POST'])
def enroll(id, user_id):
    course = Course.query.filter_by(id=id).first()
    user = User.query.filter_by(id=user_id).first()
    user.enroll(course)
    db.session.commit()
    flash("Succesfully enrolled {} into {}".format(user.username, course.title))

    return redirect(url_for('courses.users', id=id))


@bp.route('/course/<int:id>/ban/<int:user_id>', methods=['GET', 'POST'])
def ban(id, user_id):
    # you can't ban yourself
    course = Course.query.filter_by(id=id).first()
    user = User.query.filter_by(id=user_id).first()
    if(user != current_user):
        user.withdraw(course)
        db.session.commit()
        flash("Succesfully banned {} from {}".format(
            user.username, course.title))
    else:
        flash("You can't ban yourself.")
    return redirect(url_for('courses.users', id=id))
