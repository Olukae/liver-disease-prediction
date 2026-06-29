from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    IntegerField, SelectField, FloatField, TextAreaField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
)

from app.models import User


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    age = IntegerField("Age", validators=[Optional(), NumberRange(min=0, max=120)])
    gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
                          validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign In")


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Reset Password")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    age = IntegerField("Age", validators=[Optional(), NumberRange(min=0, max=120)])
    gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")])
    submit = SubmitField("Save Changes")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )
    submit = SubmitField("Update Password")


class PredictionForm(FlaskForm):
    age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=1, max=120)])
    gender = SelectField("Gender", choices=[("1", "Male"), ("0", "Female")], validators=[DataRequired()])
    total_bilirubin = FloatField("Total Bilirubin (mg/dL)", validators=[DataRequired(), NumberRange(min=0, max=80)])
    direct_bilirubin = FloatField("Direct Bilirubin (mg/dL)", validators=[DataRequired(), NumberRange(min=0, max=40)])
    alkaline_phosphotase = FloatField("Alkaline Phosphatase (IU/L)", validators=[DataRequired(), NumberRange(min=0, max=3000)])
    alt = FloatField("Alamine Aminotransferase - ALT (IU/L)", validators=[DataRequired(), NumberRange(min=0, max=3000)])
    ast = FloatField("Aspartate Aminotransferase - AST (IU/L)", validators=[DataRequired(), NumberRange(min=0, max=3000)])
    total_proteins = FloatField("Total Protein (g/dL)", validators=[DataRequired(), NumberRange(min=0, max=15)])
    albumin = FloatField("Albumin (g/dL)", validators=[DataRequired(), NumberRange(min=0, max=10)])
    ag_ratio = FloatField("Albumin and Globulin Ratio", validators=[DataRequired(), NumberRange(min=0, max=5)])
    submit = SubmitField("Run Prediction")
