from flask import Blueprint, request, jsonify, session, current_app
from models import db, User, Subscription, SUBSCRIPTION_PLANS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import os
import traceback

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
        remaining_analyses=SUBSCRIPTION_PLANS['free']['analyses_per_month'],
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    user.subscription = subscription
    
    db.session.add(user)
    db.session.commit()
    
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(days=30)},
        os.getenv('JWT_SECRET_KEY')
    )
    
    response = jsonify({
        'message': 'Usuário registrado com sucesso',
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }
    })
    response.set_cookie('token', token, httponly=True, secure=False, samesite='Lax')
    return response

@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        current_app.logger.info(f"Tentativa de login para: {data.get('email') if data else 'No data'}")
        
        if not data:
            return jsonify({'message': 'Dados não fornecidos'}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'message': 'Email e senha são obrigatórios'}), 400
            
        user = User.query.filter_by(email=email).first()
        current_app.logger.info(f"Usuário encontrado: {user is not None}")
        
        if not user:
            return jsonify({'message': 'Email ou senha inválidos'}), 401
            
        if not user.check_password(password):
            current_app.logger.info("Senha inválida")
            return jsonify({'message': 'Email ou senha inválidos'}), 401
            
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(days=30)},
            os.getenv('JWT_SECRET_KEY')
        )
        
        response = jsonify({
            'message': 'Login realizado com sucesso',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        })
        response.set_cookie('token', token, httponly=True, secure=False, samesite='Lax')
        return response
        
    except Exception as e:
        current_app.logger.error(f"Erro no login: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'message': 'Erro ao processar login',
            'error': str(e)
        }), 500

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