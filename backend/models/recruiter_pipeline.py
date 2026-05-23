from extensions import db
from datetime import datetime

class RecruiterPipeline(db.Model):
    __tablename__ = 'recruiter_pipeline'
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stage = db.Column(db.String(50), default="Sourced")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
