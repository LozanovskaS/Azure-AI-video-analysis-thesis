from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate  # Make sure this line exists
from routes.transcript_routes import transcript_bp
from routes.search_routes import search_bp
from routes.chat_routes import chat_bp
from routes.matches_routes import matches_bp
from config import Config
from models import db

#Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
app.config.from_object(Config)

#database
db.init_app(app)

#Flask-Migrate
migrate = Migrate(app, db)

#blueprints
app.register_blueprint(transcript_bp, url_prefix='/api/transcript')
app.register_blueprint(search_bp, url_prefix='/api/search')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(matches_bp, url_prefix='/api/matches') 

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        db.session.execute('SELECT 1')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status
    }

if __name__ == '__main__':
    app.run(debug=True)