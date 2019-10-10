# coding=utf-8
import io
import os
import sys
from flask import make_response, render_template, flash, redirect, url_for, request, \
    current_app
from flask_login import login_required, current_user
from app import db
from app.models import Course, Assignment, Solution, Test, Code, Template
from app.assignments import bp
from werkzeug.utils import secure_filename
from flask import jsonify
import datetime
import uuid
import time
import re

_GRADE = {'PASS': 1, 'FAIL': 2, 'PARTIAL': 3}

@bp.route("/assignment/<int:id>", methods=["GET", "POST"])
@login_required
def assignment(id):
    assignment = Assignment.query.filter_by(id=id).first_or_404()
    return render_template("assignments/assignment.html",
                           assignment=assignment)


@bp.route("/assignment/description/<int:assignment_id>", methods=["GET", "POST"])
@login_required
def description(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first_or_404()
    description = assignment.description if assignment.description else ''
    sample_input = assignment.sample_input if assignment.sample_input else ''
    sample_output = assignment.sample_output if assignment.sample_output else ''
    test_data = assignment.test_data if assignment.test_data else ''
    time_limit = assignment.time_limit if assignment.time_limit else ''

    full_description = description + \
        "\n #### Input\n" + sample_input + \
        "\n #### Output\n" + sample_output + \
        "\n #### Time limit\n" + str(time_limit) + "s"

    response = {"description": full_description, "test_data": test_data}
    return jsonify(response)


@bp.route("/course/<int:course_id>/add_assignment", methods=["GET", "POST"])
@login_required
def add_assignment(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    if request.method == 'POST':
        existing_assignment = Assignment.query.filter_by(
            title=request.form["title"]).first()
        if existing_assignment is not None:
            flash("Use different title")
            return redirect(url_for('assignments.add_assignment', course_id=course.id))

        assignment = Assignment()
        assignment.title = request.form['title']
        assignment.course = course
        assignment.description = request.form['description']
        assignment.sample_input = request.form['sample_input']
        assignment.sample_output = request.form['sample_output']
        assignment.test_data = request.form['test_data']
        if request.form['time_limit'] != '' and is_number(request.form['time_limit']):
            assignment.time_limit = request.form['time_limit']

        db.session.add(assignment)
        db.session.commit()
        flash("Successfully added new assignment to {}".format(course.title))
        return redirect(url_for("assignments.assignment", id=assignment.id))

    return render_template("assignments/add_assignment.html", title="Add assignment", course=course)


@bp.route("/assignment/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_assignment(id):
    assignment = Assignment.query.filter_by(id=id).first()
    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        assignment.sample_input = request.form['sample_input']
        assignment.sample_output = request.form['sample_output']
        assignment.test_data = request.form['test_data']
        if request.form['time_limit'] != '' and is_number(request.form['time_limit']):
            assignment.time_limit = request.form['time_limit']

        db.session.commit()
        flash("Successfully saved changes")
        return redirect(url_for("assignments.assignment", id=id))

    return render_template("assignments/edit_assignment.html",
                           title="Edit assignment",
                           assignment=assignment)


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
            solution = Solution.query.filter_by(
                assignment_id=assignment.id, is_default=True).first()
            if solution:
                solution_code = read_file(
                    solution.code.path) if solution else ""
                code = solution_code
            if code == "":
                code = template_code
        elif tab == "test":
            test = assignment.test
            test_code = read_file(test.code.path) if test else ""
            code = test_code
        else:
            code = template_code
    else:
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=False, is_submitted=False, user_id=current_user.id).first()
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
            resp = {"message": "No selected file", "status": 1}
            return jsonify(resp)

        if file and allowed_file(file.filename):
            code = file.read().decode("utf-8")
            save_code_to_file(assignment_id, tab, code)
        resp = {"message": "Succesfully uploaded file", "status": 1}
    else:
        resp = {"message": "No selected file", "status": 1}

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
        solution = Solution.query.filter_by(
            assignment_id=assignment.id, is_default=False, is_submitted=False, user_id=current_user.id).first()
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

    test_data = parse_test_data(assignment.test_data, 3)
    results = []

    for i in range(0, len(test_data["test_inputs"])):
        test = test_data["test_inputs"][i]
        output = test_data["test_outputs"][i]

        result = run_just_code(assignment, test)
        result_text = ""
        output = output.replace('\r', '').replace('\n', '').replace(' ', '')
        result_output = result["result"].replace(
            '\r', '').replace('\n', '').replace(' ', '')

        result_text = "TEST {}\nINPUT: {} \nOUTPUT: {} \nTIME: {}s".format(i +1, test, result_output, result["time"])
        results.append({'message': result_text})
        
    return jsonify(results)


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

    file = open(path, "w+", encoding='utf-8')
    file.write(code)

    if tab == "solution":
        save_solution(assignment, filename)
    elif tab == "test":
        save_test(assignment, filename)
    elif tab == "template":
        save_template(assignment, filename)


def get_filename_for_existing(tab, assignment):
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
    execution_time = 0.0

    try:
        executable = compile(code, "<string>", "exec")
        buffer = io.StringIO()
        sys.stdout = buffer
        start = time.time()
        exec(executable, locals(), locals())
        end = time.time()
        execution_time = start - end
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
    full_resp = {
        "result": resp,
        "time": execution_time
    }
    return full_resp


def read_file(path):
    contents = ""
    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], path)
    with io.open(full_path, "r", encoding='utf-8') as f:
        contents = f.read()
    return contents


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower(
           ) in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/active_solution/<int:assignment_id>", methods=["GET"])
@login_required
def active_solution(assignment_id):
    solution = Solution()
    if current_user.role.name in ['teacher', 'admin']:
        solution = Solution.query.filter_by(assignment_id=assignment_id,
                                            is_default=True).first_or_404()
    else:
        solution = Solution.query.filter_by(assignment_id=assignment_id,
                                            is_default=False, user_id=current_user.id, is_submitted=False).first_or_404()
    resp = {'id': solution.id}
    return jsonify(resp)


@bp.route("/submit", methods=["POST"])
@login_required
def submit():
    solution_id = request.form.get('solutionId')
    solution = Solution.query.filter_by(id=solution_id).first()

    assignment = solution.assignment
    test_data = parse_test_data(assignment.test_data)
    results = []

    for i in range(0, len(test_data["test_inputs"])):
        test = test_data["test_inputs"][i]
        output = test_data["test_outputs"][i]
        
        result = run_just_code(solution.assignment, test)
        result_text = ""
        grade = _GRADE["FAIL"]
        output = output.replace('\r', '').replace('\n', '').replace(' ', '')
        result_output = result["result"].replace('\r', '').replace('\n', '').replace(' ', '')

        if assignment.time_limit is not None:    
            if result_output == output:
                result_text = "Test {}: CORRECT {} == {}, ".format(
                    i + 1, result_output, output)

                if result["time"] <= assignment.time_limit:
                    grade = _GRADE["PASS"]
                    result_text = "{} AND ON TIME, TIME: {}s, TIME_LIMIT: {}s".format(result_text, result["time"], assignment.time_limit)
                else:
                    grade = _GRADE["PARTIAL"]
                    result_text = "{} BUT TOO SLOW, TIME: {}s TIME_LIMIT: {}s".format(result_text, result["time"], assignment.time_limit)
            else:
                grade = _GRADE["FAIL"]
                result_text = "Test {}: INCORRECT {} != {}, ".format(
                    i + 1, result_output, output)
        else:
            if result_output == output:
                grade = _GRADE["PASS"]
                result_text = "Test {}: CORRECT {} == {}, ".format(
                    i + 1, result_output, output)
            else:
                grade = _GRADE["FAIL"]
                result_text = "Test {}: INCORRECT {} != {}, ".format(
                    i + 1, result_output, output)

        results.append({'message': result_text, 'grade': grade})

    solution.result_text = '\n '.join([result['message'] for result in results])
    solution.is_submitted = True
    db.session.add(solution)
    db.session.commit()
    return jsonify({"result": results})


def run_just_code(assignment, test_data = None):
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
    if test_data:
        code = "{}\n{}\nprint(test({}))".format(solution_code, test_code, test_data)
    else:
        code = "{}\n{}".format(solution_code, test_code)

    result = execute_code(code)

    return result

def parse_test_data(test_data_plain_text, num_of_td = None):
    rows = test_data_plain_text.split('\n')
    test_inputs = []
    test_outputs = []
    n = len(rows) if len(rows) <= 3 else num_of_td if num_of_td != None else len(rows)
    for i in range(0, n):
        row = rows[i]
        row.replace(' ', '')
        rx = r'\[(.*?)\]'
        test_input_re_search = re.search(rx, row)
        test_input = ''
        test_output = ''

        if test_input_re_search is not None:
            test_input = row[test_input_re_search.start()
                                                        : test_input_re_search.end()]

            test_output = row.replace(test_input + ',', '')
            test_output_re_search = re.search(rx, test_output)
            if test_output_re_search is not None:
                test_output = test_output[test_output_re_search.start(
                ): test_output_re_search.end()]
        else:
            rowArray = row.split(',')
            test_input = rowArray[0]
            test_output = rowArray[1]

        test_inputs.append(test_input)
        test_output.strip('\r')
        test_outputs.append(test_output)
    return {'test_inputs': test_inputs, 'test_outputs': test_outputs}


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
