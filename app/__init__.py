from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{os.path.join(os.getcwd(), "database.db")}'
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "user_files")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from app.routes import main
app.register_blueprint(main)