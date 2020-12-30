from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, PasswordField, DateField, SelectField, RadioField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Length, EqualTo
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import Visitor, URL, User
from sqlalchemy import text

""" queries in select forms
def get_campaign_types():
    stmt = text("SELECT id, name FROM campaigntypes ORDER BY name ASC")
    stmt = stmt.columns(CampaignType.id)
    return CampaignType.query.from_statement(stmt).all()
"""

class UserLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class URLForm(FlaskForm):
    url = StringField("URL", validators=[DataRequired()])
