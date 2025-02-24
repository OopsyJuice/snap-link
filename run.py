import os
from flask.cli import FlaskGroup
from backend.app import create_app, db
from flask_migrate import Migrate
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
migrate = Migrate(app, db)

# Add this to help Flask find the app
os.environ['FLASK_APP'] = 'run.py'

cli = FlaskGroup(app)

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully")
        
        logger.info("Starting Flask server on http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")