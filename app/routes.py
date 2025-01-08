from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import emit, join_room, leave_room, rooms
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.services import save_uploaded_file, start_session, run_battle
from app import db, socketio
import os, re, shutil

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
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username must only contain letters, numbers, and underscores.')
            return redirect(url_for('main.register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('main.register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        user_folder = os.path.join("user_files", username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            default_file = os.path.join("app", "default.py")
            user_file = os.path.join(user_folder, "module.py")
            shutil.copy(default_file, user_file)

        flash('User registered successfully. You can now log in.')
        return redirect(url_for('main.index'))
    
    return render_template('register.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'py'

battle_history = {}

@socketio.on('start_battle')
def handle_start_battle():
    user_id = current_user.id
    if not user_id:
        emit('error', {'message': 'User is not logged in.'})
        return
    
    room = f"room_{user_id}"

    #current_rooms = rooms()
    #if room in current_rooms:
    #    print(f"Resetting existing session for user {user_id} in room {room}.")
    #    leave_room(room)
    
    join_room(room)
    print(f"User {user_id} started a battle in room {room}, session ID: {request.sid}")

    #for step_result in start_session(user_id):
    #    emit('game_step', step_result, room=room)

    battle_data, result = run_battle(user_id)
    emit('battle_end', {"result": result}, room=room)
    battle_history[user_id] = battle_data

@socketio.on("get_history")
def handle_get_history():
    user_id = current_user.id
    history = battle_history.get(user_id, [])
    emit("battle_history", history)

@socketio.on("connect")
def handle_connect():
    print(f"User connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = current_user.get_id()
    if user_id:
        room = f"room_{user_id}"
        print(f"User disconnected: {request.sid}, leaving room {room}")
        leave_room(room)
    else:
        print(f"User disconnected: {request.sid}, but no user_id found.")