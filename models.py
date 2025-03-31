from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription = db.relationship('Subscription', backref='user', uselist=False)
    analyses = db.relationship('Analysis', backref='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # 'free', 'premium', 'business'
    analyses_remaining = db.Column(db.Integer, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_active(self):
        return self.expires_at > datetime.utcnow()

    def can_analyze(self):
        return self.is_active and self.analyses_remaining > 0

    def use_analysis(self):
        if self.can_analyze():
            self.analyses_remaining -= 1
            return True
        return False

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cv_filename = db.Column(db.String(255))
    job_description = db.Column(db.Text)
    similarity_score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    using_ai = db.Column(db.Boolean, default=False)

SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Básico',
        'price': 0,
        'analyses_per_month': 3,
        'features': [
            'Análise por palavras-chave',
            'Score de compatibilidade',
            'Feedback básico'
        ]
    },
    'premium': {
        'name': 'Premium',
        'price': 29.90,
        'analyses_per_month': 30,
        'features': [
            'Análise com IA',
            'Feedback detalhado',
            'Histórico de análises',
            'Exportação de relatórios'
        ]
    },
    'business': {
        'name': 'Empresarial',
        'price': 99.90,
        'analyses_per_month': 100,
        'features': [
            'Tudo do Premium',
            'API de integração',
            'Suporte prioritário',
            'Análise em lote'
        ]
    }
} 