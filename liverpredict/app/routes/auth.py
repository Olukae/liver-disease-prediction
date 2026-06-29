from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, mail
from app.models import User
from app.forms import (
    RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm,
    ProfileForm, ChangePasswordForm,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            age=form.age.data,
            gender=form.gender.data,
            role="patient",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! You can now sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
            next_page = request.args.get("next")
            if user.is_admin:
                return redirect(next_page or url_for("admin.dashboard"))
            return redirect(next_page or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RequestResetForm()
    reset_link = None
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            reset_link = url_for("auth.reset_with_token", token=token, _external=True)
            try:
                from flask_mail import Message
                msg = Message(
                    "Reset Your LiverPredict AI Password",
                    recipients=[user.email],
                    body=f"Click the link to reset your password: {reset_link}\nThis link expires in 1 hour.",
                )
                mail.send(msg)
            except Exception as e:
                current_app.logger.warning(f"Email send skipped/failed: {e}")
        # Always show generic message (don't leak whether email exists)
        flash("If that email exists, a reset link has been generated below.", "info")

    return render_template("auth/request_reset.html", form=form, reset_link=reset_link)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash("That reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.request_reset"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash("Your password has been updated. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, token=token)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    pwd_form = ChangePasswordForm()

    if form.submit.data and form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.age = form.age.data
        current_user.gender = form.gender.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, pwd_form=pwd_form)


@auth_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    pwd_form = ChangePasswordForm()
    form = ProfileForm(obj=current_user)
    if pwd_form.validate_on_submit():
        if not current_user.check_password(pwd_form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(pwd_form.new_password.data)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("auth.profile"))
    else:
        for errors in pwd_form.errors.values():
            for e in errors:
                flash(e, "danger")
    return render_template("auth/profile.html", form=form, pwd_form=pwd_form)
