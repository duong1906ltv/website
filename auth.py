from hashlib import sha256
from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import ChangePasswordForm,PasswordResetForm,PasswordResetRequestForm
from .email import send_mail
auth = Blueprint("auth", __name__)



@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        email_exists = User.query.filter_by(email=email).first()
        username_exists = User.query.filter_by(username=username).first()

        if email_exists:
            flash('Email is already in use.', category='error')
        elif username_exists:
            flash('Username is already in use.', category='error')
        elif password1 != password2:
            flash('Password don\'t match!', category='error')
        elif len(username) < 2:
            flash('Username is too short.', category='error')
        elif len(password1) < 6:
            flash('Password is too short.', category='error')
        elif len(email) < 4:
            flash("Email is invalid.", category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            subject = "Confirm your email"
            token = new_user.generate_confirmation_token()
            confirm_url = url_for(
            'auth.confirm',
            token=token,
            _external=True)
            html = render_template('activate.html', user = new_user, confirm_url = confirm_url)
            send_mail(new_user.email,subject,html)
            login_user(new_user)
            flash('A confirmation email has been sent via email.', 'success')
            return redirect(url_for('auth.unconfirmed'))

    return render_template("signup.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('views.home'))
    return render_template('auth/unconfirmed.html')
@auth.route('/confirm')
@login_required
def resend_confirmation():
    subject = "Confirm your email"
    token = current_user.generate_confirmation_token()
    confirm_url = url_for(
    'auth.confirm',
    token=token,
    _external=True)
    html = render_template('activate.html', user = current_user, confirm_url = confirm_url)
    send_mail(current_user.email,subject,html)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('views.home'))

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('views.home'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('views.home'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pass = request.form.get("old_pass")
        new_pass = request.form.get("new_pass")
        user = User.query.filter_by(id=current_user.id).first()
        if old_pass:
            current_user.password = generate_password_hash(new_pass)
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('views.home'))
        else:
            flash('Invalid password.')
    else:
        print("Some thing wrong")
    return render_template("change_password.html")

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email_address.data).first()
        if user:
            subject = "Confirm your email"
            token = user.generate_confirmation_token()
            confirm_url = url_for(
            'auth.password_reset',
            token=token,
            _external=True)
            html = render_template('activate.html', user = user, confirm_url = confirm_url)
            send_mail(user.email,subject,html)
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', form=form)

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email_address.data).first()
        if user is None:
            return redirect(url_for('views.home'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('views.home'))
    return render_template('reset_password.html', form=form)

