from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(50))  # "mentor" or "learner"
    skills = db.Column(db.String(200))
    bio = db.Column(db.Text)
    rating = db.Column(db.Float, default=0.0)

class SessionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    topic = db.Column(db.String(200))
    message = db.Column(db.Text)

    learner = db.relationship('User', foreign_keys=[learner_id])
    mentor = db.relationship('User', foreign_keys=[mentor_id])

    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100))
    message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, sender, message):
        self.sender = sender
        self.message = message
