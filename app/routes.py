from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import emit, join_room
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.services import save_uploaded_file, start_session
from app import db, socketio

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')  # トップページ (ログインフォーム)

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
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part.")
            return redirect(url_for('main.home'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(url_for('main.home'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_uploaded_file(filename, current_user.id)
            flash('File uploaded successfully.')
        else:
            flash('Invalid file type. Only .py files are allowed.')
        return redirect(url_for('main.home'))
    return render_template('home.html')  # ホーム画面

@main.route('/battle', methods=['GET'])
@login_required
def battle():
    return render_template('battle.html')

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'py'

@socketio.on('start_battle')
def handle_start_battle():
    user_id = current_user.id
    if not user_id:
        emit('error', {'message': 'User is not logged in.'})
        return
    
    room = f"room_{user_id}"
    join_room(room)

    for step_result in start_session(user_id):
        emit('game_step', step_result, room=room)

    emit('game_end', {"message": "Game Over"}, room=room)