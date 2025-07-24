from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class CallRecord(db.Model):
    __tablename__ = 'call_records'
    
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(64), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    caller_name = db.Column(db.String(255), nullable=True)
    tenant_unit = db.Column(db.String(50), nullable=True)
    tenant_id = db.Column(db.String(50), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # seconds
    recording_url = db.Column(db.String(500), nullable=True)
    transcription = db.Column(db.Text, nullable=True)
    call_status = db.Column(db.String(20), default='active')  # active, completed, failed
    conversation_summary = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<CallRecord {self.phone_number} - {self.start_time}>'

class ActiveCall(db.Model):
    __tablename__ = 'active_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    call_sid = db.Column(db.String(64), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    caller_name = db.Column(db.String(255), nullable=True)
    tenant_unit = db.Column(db.String(50), nullable=True)
    tenant_id = db.Column(db.String(50), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    call_status = db.Column(db.String(20), default='ringing')  # ringing, connected, on_hold
    current_action = db.Column(db.String(255), nullable=True)  # what Chris is doing
    
    def __repr__(self):
        return f'<ActiveCall {self.phone_number} - {self.caller_name or "Unknown"}>'