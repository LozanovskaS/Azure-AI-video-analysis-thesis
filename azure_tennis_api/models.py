from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
import enum

db = SQLAlchemy()

class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    players = db.Column(ARRAY(db.String), nullable=True)  
    tournament = db.Column(db.String(200))
    match_date = db.Column(db.Date)
    surface = db.Column(db.String(20))  # clay, hard, grass
    processing_status = db.Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    transcript_blob_url = db.Column(db.Text)
    azure_search_indexed = db.Column(db.Boolean, default=False)
    duration_seconds = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'players': self.players,
            'tournament': self.tournament,
            'match_date': self.match_date.isoformat() if self.match_date else None,
            'surface': self.surface,
            'processing_status': self.processing_status.value if self.processing_status else None,
            'azure_search_indexed': self.azure_search_indexed,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'error_message': self.error_message
        }

class AnalysisSession(db.Model):
    __tablename__ = 'analysis_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    source_match_ids = db.Column(ARRAY(db.Integer))  
    processing_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'ai_response': self.ai_response,
            'source_match_ids': self.source_match_ids,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat()
        }