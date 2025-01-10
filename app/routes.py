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
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part.")
            return redirect(url_for('main.home'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(url_for('main.home'))
        
        if file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_uploaded_file(filename, current_user.id)
            flash('File uploaded successfully.')
        else:
            flash('Invalid file type. Only .py files are allowed.')
        return redirect(url_for('main.home'))
    """

    user_folder = os.path.join("user_files", current_user.username)
    os.makedirs(user_folder, exist_ok=True)
    user_files = [f for f in os.listdir(user_folder) if f.endswith(".py")]

    selected_file = request.args.get("file", "module.py")
    selected_file_path = os.path.join(user_folder, selected_file)
    initial_file_content = ""
    if os.path.exists(selected_file_path):
        with open(selected_file_path, "r") as f:
            initial_file_content = f.read()

    return render_template('home.html', user_files=user_files, initial_file_content=initial_file_content)  # ホーム画面

@main.route("/update-file", methods=["POST"])
@login_required
def update_module():
    data = request.form
    file_name = data.get("file_selector", "module.py")
    content = data.get("editor", "")

    user_folder = os.path.join("user_files", current_user.username)
    file_path = os.path.join(user_folder, file_name)
    with open(file_path, "w") as f:
        f.write(content)

    flash("File saved successfully.")
    return redirect(url_for("home"))

@main.route("/file-manager", methods=["GET"])
@login_required
def file_manager():
    user_folder = os.path.join("user_files", current_user.username)
    os.makedirs(user_folder, exist_ok=True)
    files = []
    for file_name in os.listdir(user_folder):
        file_path = os.path.join(user_folder, file_name)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path) / 1024
            files.append({"name": file_name, "size": round(size, 2)})

    return render_template("file_manager.html", files=files)
@main.route("/upload-file", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("file")
    if file and file.filename.endswith(".py"):
        user_folder = os.path.join('user_files', current_user.username)
        os.makedirs(user_folder, exist_ok=True)

        # フォルダ内の総容量を計算
        total_size = sum(os.path.getsize(os.path.join(user_folder, f)) for f in os.listdir(user_folder))
        if total_size + len(file.read()) > 5 * 1024 * 1024:  # 5MB制限
            flash('Total folder size exceeds 5MB. Upload failed.', 'error')
            return redirect(url_for('file_manager'))

        file.seek(0)  # ファイルポインタを先頭に戻す
        file.save(os.path.join(user_folder, secure_filename(file.filename)))
        flash('File uploaded successfully.')
    else:
        flash('Only .py files are allowed.', 'error')
    return redirect(url_for('file_manager'))

# ファイル削除処理
@main.route('/delete-file', methods=['POST'])
@login_required
def delete_file():
    file_name = request.form.get('file_name')
    user_folder = os.path.join('user_files', current_user.username)
    file_path = os.path.join(user_folder, file_name)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash('File deleted successfully.')
    else:
        flash('File not found.', 'error')
    return redirect(url_for('file_manager'))

# ファイル編集処理（ファイル管理からホームへ遷移）
@main.route('/edit-file', methods=['POST'])
@login_required
def edit_file():
    file_name = request.form.get('file_name')
    return redirect(url_for('home', file=file_name))

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