from flask import Flask, render_template, redirect, url_for, request, flash
from models import User, db
from flask_login import LoginManager, login_user, logout_user, login_required

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dream_db.sqlite'

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'index'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("index"))
        flash("Неверный логин или пароль")
    return render_template("login.html")

# ф-ция регистрации
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("reg_username")
        password = request.form.get("reg_password")
        password2 = request.form.get("reg_password2")
        if password != password2:
            flash("Пароли не совпадают")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("Пользователь уже существует")
            return redirect(url_for("register"))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Регистрация прошла успешно. Войдите в аккаунт")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
