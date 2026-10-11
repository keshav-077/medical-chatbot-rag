from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, nullable=False)  # True for user message, False for assistant
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    citations_json = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(32), nullable=True)
    trace_id = db.Column(db.String(80), nullable=True)
    intent = db.Column(db.String(32), nullable=True)


class UserHealthProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    allergies = db.Column(db.Text, default="")
    conditions = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    google_refresh_token = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('health_profile', uselist=False))


class UserMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    dose = db.Column(db.String(120), default="")
    frequency = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('medications', lazy=True, cascade='all, delete-orphan'))


class DrugMonograph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    generic_name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    brand_names = db.Column(db.String(400), default="")
    composition = db.Column(db.Text, nullable=False)
    uses = db.Column(db.Text, default="")
    warnings = db.Column(db.Text, default="")
    interactions = db.Column(db.Text, default="")
    source = db.Column(db.String(200), default="")
    document_date = db.Column(db.String(32), default="")
    country = db.Column(db.String(8), default="IN")
    section = db.Column(db.String(64), default="monograph")
    content_hash = db.Column(db.String(64), default="")


class UserFavoritePlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    place_id = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    kind = db.Column(db.String(32), nullable=False)
    address = db.Column(db.String(400), default="")
    phone = db.Column(db.String(40), default="")
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    user = db.relationship('User', backref=db.backref('favorite_places', lazy=True, cascade='all, delete-orphan'))


class UploadedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(500), nullable=False)
    doc_type = db.Column(db.String(32), default="lab")
    status = db.Column(db.String(32), default="uploaded")
    extracted_text = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('documents', lazy=True, cascade='all, delete-orphan'))


class LabResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('uploaded_document.id'), nullable=True)
    summary = db.Column(db.Text, default="")
    rows_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    document = db.relationship('UploadedDocument', backref=db.backref('lab_results', lazy=True))


class AppointmentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    specialty = db.Column(db.String(120), default="")
    reason = db.Column(db.Text, default="")
    preferred_times = db.Column(db.String(300), default="")
    place_id = db.Column(db.String(200), default="")
    place_name = db.Column(db.String(200), default="")
    phone = db.Column(db.String(40), default="")
    status = db.Column(db.String(32), default="draft")
    remind_at = db.Column(db.DateTime, nullable=True)
    reminded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('appointments', lazy=True, cascade='all, delete-orphan'))


class IngestJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(120), nullable=False)
    content_hash = db.Column(db.String(64), default="")
    status = db.Column(db.String(32), default="ok")
    detail = db.Column(db.Text, default="")
    ran_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    rating = db.Column(db.String(8), nullable=False)
    trace_id = db.Column(db.String(80), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ShareToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(80), unique=True, nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    kind = db.Column(db.String(32), default="info")
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))