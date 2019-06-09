import io
import os
import sys
from flask import render_template, flash, redirect, url_for, request, \
    current_app
from flask_login import login_required, current_user
from app import db

from app.models import Course, Assignment, Solution, Test, Code, Template
from app.assignments import bp
from werkzeug.utils import secure_filename
from flask import jsonify
import datetime
import uuid

@bp.route("/assignment/<int:id>", methods=["GET", "POST"])
@login_required
def assignment(id):
    assignment = Assignment.query.filter_by(id=id).first_or_404()
    return render_template("assignments/assignment.html",
                           assignment=assignment)


@bp.route("/course/<int:course_id>/add_assignment", methods=["GET", "POST"])
@login_required
def add_assignment(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()

    assignment = Assignment(title=request.form["title"], description=request.form["description"], course=course)

    db.session.add(assignment)
    db.session.commit()
    flash("Successfully added new assignment to {}".format(course.title))
    return redirect(url_for("assignments.assignment", id=assignment.id))

    return render_template("assignments/add_assignment.html", title="Add assignment", course=course)


@bp.route("/assignment/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_assignment(id):
    assignment = Assignment.query.filter_by(id=id).first()
    form = AddAssignmentForm()
    if form.validate_on_submit():
        assignment.title = form.title.data
        assignment.description = form.description.data
        db.session.commit()
        flash("Successfully saved changes")
        return redirect(url_for("assignments.assignment", id=id, message="Successfully saved changes"))
    elif request.method == "GET":
        form.title.data = assignment.title
        form.description.data = assignment.description
    return render_template("assignments/edit_assignment.html",
                           title="Edit assignment",
                           form=form)


@bp.route("/editor/<int:assignment_id>", methods=["GET"])
@login_required
def editor(assignment_id):
    tab = request.args.get("tab")
    code = ""
    solution = None
    
    assignment = Assignment.query.filter_by(id=assignment_id).first()

    template = assignment.template
    template_code = read_file(template.code.path) if template else ""
    
    if current_user.role.name in ["teacher", "admin"]:
        if tab == "solution":
            solution = Solution.query.filter_by(assignment_id=assignment.id, is_default=True).first()
        elif tab == "test":
            test = assignment.test
            test_code = read_file(test.code.path) if test else ""
            code = test_code
        else:
            template = assignment.template
            template_code = read_file(template.code.path) if template else ""
            code = template_code
            
    else:
        solution = Solution.query.filter_by(assignment_id=assignment.id, is_default=False, user_id=current_user.id).first()

    if solution:
        solution_code = read_file(solution.code.path) if solution else ""
        code = solution_code
    if code == "":
        code = template_code

    return render_template("editor.html", assignment=assignment, code=code, solution=solution)


@bp.route("/upload_file", methods=["POST", "GET"])
@login_required
def upload_file():
    resp = {}
    if request.method == "POST":
        tab = request.form.get("tab")
        assignment_id = request.form.get("assignment_id")

        if "file" not in request.files:
            resp = {"message": "No file part", "status": 1}
            return jsonify(resp)
    
        file = request.files["file"]

        if file.filename == "":
            resp= {"message":"No selected file", "status": 1}
            return jsonify(resp)

        if file and allowed_file(file.filename):
            code = file.read().decode("utf-8")
            print(code)
            save_code_to_file(assignment_id, tab, code)
    else:
        resp= {"message":"No selected file", "status": 1}
        return jsonify(resp)


def save_solution(assignment, path):
    code = Code()
    solution = Solution()
    
    if current_user.role.name in ["teacher", "admin"]:
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=True).first()
        if not solution:
            solution = Solution()
            solution.is_default = True
    else:
        solution = Solution.query.filter_by(assignment_id=assignment.id, is_default=False, user_id=current_user.id).first()
        if not solution:
            solution = Solution()
            solution.is_default = False

    solution.set_user(current_user)
    solution.set_assignment(assignment)
    
    # no multiple solutions only one code..
    if solution and solution.code:
        code = solution.code
    
    code.path = path
    solution.set_code(code)

    db.session.add(assignment)
    db.session.add(code)
    db.session.add(solution)
    db.session.commit()


def save_test(assignment, path):
    code = Code()

    if assignment.test:
        test = assignment.test
        if test.code:
            code = test.code
        else:
            code.path = path
    else:
        test = Test()
        assignment.set_test(test)
        code.path = path

    test.set_code(code)
    db.session.add(code)
    db.session.add(test)
    db.session.add(assignment)
    db.session.commit()


def save_template(assignment, path):
    code = Code()

    if assignment.template:
        template = assignment.template
        if template.code:
            code = template.code
        else:
            code.path = path
    else:
        template = Template()
        assignment.set_template(template)
        code.path = path

    template.set_code(code)
    db.session.add(code)
    db.session.add(template)
    db.session.add(assignment)
    db.session.commit()


@bp.route("/save_code/<int:assignment_id>", methods=["POST"])
@login_required
def save_code(assignment_id):
    if request.method == "POST":
        code = request.form.get("code")
        tab = request.form.get("tab")
        save_code_to_file(assignment_id, tab, code)
    return "OK"

@bp.route("/run_code/<int:assignment_id>", methods=["POST"])
@login_required
def run_code(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first()

    # todo@tome handle if first time and no solution or test
    # maybe disallow run without test or solution
    solution = None
    solution_code = ""

    if current_user.role.name in ["teacher", "admin"]:
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=True).first()        
    else:
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=False, is_submitted=False, user_id=current_user.id).first()

    if solution:
        solution_code = read_file(solution.code.path)

    test_code = ""
    if assignment.test:
        test_code = read_file(assignment.test.code.path)

    code = solution_code + "\n" + test_code

    return execute_code(code)


def save_code_to_file(assignment_id, tab, code):
        assignment = Assignment.query.filter_by(id=assignment_id).first()
        filename = ""

        if tab == "solution":
            filename = get_filename_for_existing_solution(assignment)
        elif tab == "test":
            filename = get_filename_for_existing_test(assignment)
        elif tab == "template":
            filename = get_filename_for_existing_template(assignment)

        if filename != "":
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        else:
            filename = secure_filename("{}.py".format(str(uuid.uuid4())))
            file_path = current_app.config["UPLOAD_FOLDER"]
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            path = os.path.join(file_path, filename)

        file = open(path, "w+")
        file.write(code)

        if tab == "solution":
            save_solution(assignment, filename)
        elif tab == "test":
            save_test(assignment, filename)
        elif tab == "template":
            save_template(assignment, filename)


def get_filename_for_existing_solution(assignment):
    filename = ""
    solution = None
    if current_user.role.name in ["teacher", "admin"]:
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=True).first()
        if solution:
            filename = solution.code.path
    else:
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=False, is_submitted=False, user_id=current_user.id).first()
        if solution:
            filename = solution.code.path
    return filename


def get_filename_for_existing_test(assignment):
    filename = ""
    test = None
    if current_user.role.name in ["teacher", "admin"]:
        test = assignment.test
        if test:
            filename = test.code.path
    return filename


def get_filename_for_existing_template(assignment):
    filename = ""
    template = None
    if current_user.role.name in ["teacher", "admin"]:
        template = assignment.template
        if template:
            filename = template.code.path
    return filename

def execute_code(code):
    resp = ""
    try:
        executable = compile(code, "<string>", "exec")
        buffer = io.StringIO()
        sys.stdout = buffer
        exec(executable, locals(), locals())
        sys.stdout = sys.__stdout__
        resp = buffer.getvalue()
    except IOError as ioe:
        resp = str(ioe)
    except ValueError as ve:
        resp = str(ve)
    except ImportError as ie:
        resp = str(ie)
    except EOFError as eof:
        resp = str(eof)
    except SyntaxError as se:
        resp = str(se)
    except AssertionError as asse:
        resp = str(asse)
    except NameError as ne:
        resp = str(ne)
    except TypeError as te:
        resp = str(te)
    except:
        resp = "An error occurred."
    
    return resp

def read_file(path):
    contents = ""
    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], path)
    with io.open(full_path, "r") as f:
        contents = f.read()
    return contents

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower(
           ) in current_app.config["ALLOWED_EXTENSIONS"]
