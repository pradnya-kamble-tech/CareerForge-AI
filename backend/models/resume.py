from datetime import datetime
from extensions import db

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255))
    ats_score = db.Column(db.Integer)
    domain = db.Column(db.String(100))
    parsed_data = db.Column(db.Text)  # JSON string
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref=db.backref('resumes', lazy=True))

    def __repr__(self):
        return f'<Resume {self.filename} (Score: {self.ats_score})>'
