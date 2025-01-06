from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.services import save_uploaded_file, start_battle
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')  # トップページ (ログインフォーム)

@main.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        if 'file' in request.files:
            save_uploaded_file(request.files['file'], current_user.id)
            flash('File uploaded successfully.')
        elif 'start_battle' in request.form:
            pyr_wins = start_battle(current_user.id)
            if pyr_wins is None:
                flash("Canceled.")
            elif pyr_wins:
                flash("You Win!")
            else:
                flash("You Lose.")
        return redirect(url_for('main.home'))
    return render_template('home.html')  # ホーム画面

@main.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for("main.home"))
    else:
        flash("Invalid username or password")
        return redirect(url_for("main.index"))
    
@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and Password are required.')
            return redirect(url_for('main.register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('main.register'))
        
        new_user = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully. You can now log in.')
        return redirect(url_for('main.index'))
    
    return render_template('register.html')