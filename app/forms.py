# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, SubmitField
from wtforms.validators import Optional

class SearchForm(FlaskForm):
    query = StringField('Query', validators=[Optional()])
    categories = SelectMultipleField('Categories', choices=[], coerce=str, validators=[Optional()], default=[])
    tools = SelectMultipleField('Tools', choices=[], coerce=str, validators=[Optional()], default=[])
    parts = SelectMultipleField('Parts', choices=[], coerce=str, validators=[Optional()], default=[])
    submit = SubmitField('Apply Filters')
