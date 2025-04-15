from flask import Flask
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'g!Y3$gUz4z#@kF^bT*1p9WvQe@f!z2Rx'  # Replace with a secure key

# MongoDB connection
client = MongoClient('mongodb+srv://nitishmeesi:rlGiBPTXaLHBpGDC@flask.cii4wgd.mongodb.net/?retryWrites=true&w=majority&appName=flask')
db = client['forumApp']

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'forum.login'  # Redirect to login if not authenticated

from forum.models import User

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

from forum.views import bp as forum_bp
app.register_blueprint(forum_bp, url_prefix='/')
