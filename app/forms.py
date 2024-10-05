from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    submit = SubmitField('Search')