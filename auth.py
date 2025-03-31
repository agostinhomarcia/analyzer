from flask import Blueprint, request, jsonify, session
from models import db, User, Subscription, SUBSCRIPTION_PLANS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os

auth = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        
        if not token:
            return jsonify({'message': 'Token não encontrado'}), 401
        
        try:
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token inválido'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Dados incompletos'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email já cadastrado'}), 400
        
    user = User(
        email=data['email'],
        name=data.get('name', '')
    )
    user.set_password(data['password'])
    
    # Create free subscription
    subscription = Subscription(
        plan_type='free',
        analyses_remaining=SUBSCRIPTION_PLANS['free']['analyses_per_month'],
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    user.subscription = subscription
    
    db.session.add(user)
    db.session.commit()
    
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(days=30)},
        os.getenv('JWT_SECRET_KEY')
    )
    
    response = jsonify({'message': 'Usuário registrado com sucesso'})
    response.set_cookie('token', token, httponly=True, secure=True)
    return response

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Dados incompletos'}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Email ou senha inválidos'}), 401
        
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(days=30)},
        os.getenv('JWT_SECRET_KEY')
    )
    
    response = jsonify({'message': 'Login realizado com sucesso'})
    response.set_cookie('token', token, httponly=True, secure=True)
    return response

@auth.route('/logout')
def logout():
    response = jsonify({'message': 'Logout realizado com sucesso'})
    response.set_cookie('token', '', expires=0)
    return response

@auth.route('/me')
@token_required
def me(current_user):
    subscription = current_user.subscription
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'subscription': {
            'plan': subscription.plan_type,
            'analyses_remaining': subscription.analyses_remaining,
            'expires_at': subscription.expires_at.isoformat(),
            'is_active': subscription.is_active
        }
    }) 