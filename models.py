from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription = db.relationship('Subscription', backref='user', uselist=False)
    analyses = db.relationship('Analysis', backref='user', lazy=True)

    def set_password(self, password):
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password, salt)
        self.password_hash = password_hash.decode('utf-8')

    def check_password(self, password):
        if not self.password_hash:
            return False
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(self.password_hash, str):
            stored_hash = self.password_hash.encode('utf-8')
        else:
            stored_hash = self.password_hash
        try:
            return bcrypt.checkpw(password, stored_hash)
        except Exception as e:
            print(f"Erro ao verificar senha: {e}")
            return False

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(50), default='free')  # free, premium, business
    remaining_analyses = db.Column(db.Integer, default=3)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stripe_subscription_id = db.Column(db.String(255))
    status = db.Column(db.String(50), default='active')

    def can_analyze(self):
        """Verifica se o usuário pode fazer mais análises"""
        if not self.expires_at or self.expires_at < datetime.utcnow():
            return False
        
        if self.plan_type == 'business':
            return True
        
        return self.remaining_analyses > 0

    def use_analysis(self):
        """Registra o uso de uma análise"""
        if self.plan_type != 'business' and self.remaining_analyses > 0:
            self.remaining_analyses -= 1
            db.session.commit()

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