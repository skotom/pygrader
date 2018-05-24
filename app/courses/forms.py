from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from app.models import Course


class AddCourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(AddCourseForm, self).__init__(*args, **kwargs)

    def validate_title(self, title):
        course = Course.query.filter_by(title=title.data).first()
        if course is not None:
            raise ValidationError('Please use a different title.')


class EditCourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EditCourseForm, self).__init__(*args, **kwargs)
