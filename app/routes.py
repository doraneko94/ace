from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from flask_socketio import emit, join_room, leave_room, rooms
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.services import save_uploaded_file, start_session, run_battle
from app.utils import confirm_token, generate_confirmation_token
from app import app, db, mail, socketio
import os, re, shutil

main = Blueprint('main', __name__)
limiter = Limiter(get_remote_address, app=app)

@main.route('/')
def index():
    return render_template('index.html')  # トップページ (ログインフォーム)

@main.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        if not user.is_confirmed:
            flash('Please confirm your email address before logging in.', 'error')
            return redirect(url_for('main.index'))
        else:
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

    return render_template('home.html', selected_file=selected_file, user_files=user_files, initial_file_content=initial_file_content)  # ホーム画面

@main.route('/get-file-content', methods=['GET'])
@login_required
def get_file_content():
    file_name = request.args.get('file', '').strip()  # リクエストからファイル名を取得
    user_folder = os.path.join('user_files', current_user.username)
    file_path = os.path.join(user_folder, file_name)

    # ファイルの存在を確認
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({"error": "File not found."}), 404

    # ファイル内容を読み込む
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return jsonify({"content": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/create-new-file', methods=['POST'])
@login_required
def create_new_file():
    data = request.json
    file_name = data.get('file_name', '').strip()

    # ファイル名が空でないか確認
    if not file_name:
        return jsonify({'success': False, 'error': 'File name cannot be empty.'}), 400

    # ファイル名が `.py` で終わらない場合に `.py` を追加
    if not file_name.endswith('.py'):
        file_name += '.py'

    user_folder = os.path.join('user_files', current_user.username)
    os.makedirs(user_folder, exist_ok=True)

    # ファイル名の重複チェック
    file_path = os.path.join(user_folder, file_name)
    if os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'A file with this name already exists.'}), 400

    content = '# New Python file\n'
    # 新しいファイルを作成
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return jsonify({'success': True, "content": content}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/update-file", methods=["POST"])
@login_required
def update_module():
    data = request.json
    file_name = secure_filename(data.get("file_name", ""))
    content = data.get("content", "")

    user_folder = os.path.join("user_files", current_user.username)
    file_path = os.path.join(user_folder, file_name)

    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": "File not found."}), 404
    
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
            return redirect(url_for('main.file_manager'))

        file.seek(0)  # ファイルポインタを先頭に戻す
        file.save(os.path.join(user_folder, secure_filename(file.filename)))
        flash('File uploaded successfully.')
    else:
        flash('Only .py files are allowed.', 'error')
    return redirect(url_for('main.file_manager'))

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
    return redirect(url_for('main.file_manager'))

# ファイル編集処理（ファイル管理からホームへ遷移）
@main.route('/edit-file', methods=['POST'])
@login_required
def edit_file():
    file_name = request.form.get('file_name')
    return redirect(url_for('main.home', file=file_name))

@main.route('/battle', methods=['GET'])
@login_required
def battle():
    return render_template('battle.html')

def validate_username(username):
    if len(username) < 3 or len(username) > 20:
        return 'Username must be between 3 and 20 characters.'
    if not re.match("^[A-Za-z0-9_]+$", username):
        return 'Username can only contain letters, numbers, and underscores.'
    return None

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."
    return None

def validate_email(email):
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return 'Invalid email address.'
    return None

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('This email is already registered.', 'error')
            return redirect(url_for('main.register'))

        if not username or not password:
            flash('Username and Password are required.')
            return redirect(url_for('main.register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.', 'error')
            return redirect(url_for('main.register'))
        
        username_error = validate_username(username)
        password_error = validate_password(password)
        email_error = validate_email(email)
        
        if username_error or password_error or email_error:
            flash(username_error or password_error or email_error, "error")
            return redirect(url_for("main.register"))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, is_confirmed=False)
        db.session.add(new_user)
        db.session.commit()

        token = generate_confirmation_token(email)
        confirm_url = url_for('main.confirm_email', token=token, _external=True)
        html = render_template('email_confirmation.html', confirm_url=confirm_url)

        msg = Message('Confirm Your Email', recipients=[email], html=html)
        mail.send(msg)

        user_folder = os.path.join("user_files", username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            default_file = os.path.join("app", "default.py")
            user_file = os.path.join(user_folder, "module.py")
            shutil.copy(default_file, user_file)

        flash('A confirmation email has been sent. Please check your inbox.', 'info')
        return redirect(url_for('main.index'))
    
    return render_template('register.html')

@main.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for("main.index"))
    
    user = User.query.filter_by(email=email).first_or_404()

    if user.is_confirmed:
        flash('Account already confirmed. Please log in.', 'info')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')

    return redirect(url_for('main.index'))

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