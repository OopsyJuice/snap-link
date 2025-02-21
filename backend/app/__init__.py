from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from backend.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    app.config.from_object(Config)
    
    db.init_app(app)
    
    from backend.app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app