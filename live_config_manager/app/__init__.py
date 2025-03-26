from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
from config import Config
from flask_socketio import SocketIO
from .routes import start_message_processor

socketio = SocketIO()

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    # 启动消息处理线程
    with app.app_context():
        start_message_processor()
    
    return app
