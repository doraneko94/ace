from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
import os, secrets

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{os.path.join(os.getcwd(), "database.db")}'
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "user_files")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPSを使用する場合
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScriptでアクセス不可
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # クロスサイトリクエストの制限

csrf = CSRFProtect(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'main.index'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

socketio = SocketIO(app, cors_allowed_origins="*")

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from app.routes import main
app.register_blueprint(main)