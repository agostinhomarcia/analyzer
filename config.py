import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev')
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = False  # Set to True in production
    JWT_COOKIE_CSRF_PROTECT = False  # Set to True in production
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Stripe
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Subscription Plans
    SUBSCRIPTION_PLANS = {
        'free': {
            'name': 'Gratuito',
            'price': 0,
            'analyses_per_month': 3,
            'features': ['Análise básica'],
            'stripe_price_id': None
        },
        'premium': {
            'name': 'Premium',
            'price': 29.90,
            'analyses_per_month': 20,
            'features': ['Análise detalhada', 'IA avançada'],
            'stripe_price_id': os.getenv('STRIPE_PREMIUM_PRICE_ID')
        },
        'business': {
            'name': 'Business',
            'price': 99.90,
            'analyses_per_month': float('inf'),  # Unlimited
            'features': ['Análises ilimitadas', 'Análise premium', 'IA avançada', 'Suporte prioritário'],
            'stripe_price_id': os.getenv('STRIPE_BUSINESS_PRICE_ID')
        }
    } 