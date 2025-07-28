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


class RequestHistory(db.Model):
    __tablename__ = 'request_history'
    
    id = db.Column(db.Integer, primary_key=True)
    request_title = db.Column(db.String(200), nullable=False)
    request_description = db.Column(db.Text, nullable=True)
    implementation_details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, complete, failed
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime, nullable=True)
    source = db.Column(db.String(50), default='user_input')  # user_input, automatic, complaint
    category = db.Column(db.String(50), nullable=True)  # bug_fix, feature_request, enhancement, complaint
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_title': self.request_title,
            'request_description': self.request_description,
            'implementation_details': self.implementation_details,
            'status': self.status,
            'priority': self.priority,
            'date_requested': self.date_requested.isoformat() if self.date_requested else None,
            'date_completed': self.date_completed.isoformat() if self.date_completed else None,
            'source': self.source,
            'category': self.category
        }
    
    def __repr__(self):
        return f'<RequestHistory {self.request_title} - {self.status}>'