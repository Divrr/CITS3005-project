from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    categories = SelectMultipleField('Categories', choices=[], coerce=str)
    tools = SelectMultipleField('Tools', choices=[], coerce=str)
    parts = SelectMultipleField('Parts', choices=[], coerce=str)
    submit = SubmitField('Search')
