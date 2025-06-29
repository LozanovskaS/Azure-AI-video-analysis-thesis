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

class UserRole(enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    PLAYER = "player"

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    subscription_plan = db.Column(db.String(50), default='free')
    max_matches = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='team', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subscription_plan': self.subscription_plan,
            'max_matches': self.max_matches,
            'created_at': self.created_at.isoformat(),
            'user_count': len(self.users)
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    role = db.Column(db.Enum(UserRole), default=UserRole.PLAYER)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    matches = db.relationship('Match', backref='user', lazy=True)
    analysis_sessions = db.relationship('AnalysisSession', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value if self.role else None,
            'team_id': self.team_id,
            'created_at': self.created_at.isoformat(),
            'match_count': len(self.matches)
        }

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
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
            'user_id': self.user_id,
            'error_message': self.error_message
        }

class AnalysisSession(db.Model):
    __tablename__ = 'analysis_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    source_match_ids = db.Column(ARRAY(db.Integer))  
    processing_time_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question,
            'ai_response': self.ai_response,
            'source_match_ids': self.source_match_ids,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat()
        }

class ProcessingJob(db.Model):
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(50), nullable=False)
    job_type = db.Column(db.String(50))
    status = db.Column(db.Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    progress_percentage = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'job_type': self.job_type,
            'status': self.status.value if self.status else None,
            'progress_percentage': self.progress_percentage,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }