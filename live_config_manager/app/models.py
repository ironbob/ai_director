from datetime import datetime
from app import db
from flask import current_app
import os
import json

class SimpleApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    app_name = db.Column(db.String(100), nullable=False)
    config_filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_config_content(self):
        if not self.config_filename:
            return None
        try:
            with open(os.path.join(current_app.config['UPLOAD_FOLDER'], self.config_filename), 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
