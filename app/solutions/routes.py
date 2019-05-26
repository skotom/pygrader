from flask import render_template, flash, redirect, url_for, request, \
    current_app
from flask_login import login_required, current_user
from app import db
from app.models import Solution
from app.solutions import bp
from flask import jsonify

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
    resp = {id: solution.id}
    return jsonify(resp)

@bp.route("/submit", methods=["POST"])
@login_required
def submit():
    solution_id = request.form.get('solutionId')
    solution = Solution.query.filter_by(id=solution_id)
    solution.is_submitted = True
    db.session.add(solution)
    db.session.commit()
    return "OK"
