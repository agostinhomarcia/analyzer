import os
from flask import Blueprint, jsonify, request, current_app
import stripe
from models import db, User, Subscription
from auth import token_required
from datetime import datetime, timedelta

subscription = Blueprint('subscription', __name__)

# Configurar Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@subscription.route('/plans', methods=['GET'])
def get_plans():
    """Retorna os planos disponíveis"""
    return jsonify({
        'plans': [
            {
                'id': 'free',
                'name': 'Gratuito',
                'price': 0,
                'period': 'mês',
                'features': [
                    '3 análises por mês',
                    'Análise básica',
                    'Sem IA avançada'
                ]
            },
            {
                'id': 'premium',
                'name': 'Premium',
                'price': 29.90,
                'period': 'mês',
                'features': [
                    '20 análises por mês',
                    'Análise detalhada',
                    'IA avançada'
                ],
                'stripe_price_id': os.getenv('STRIPE_PRICE_PREMIUM')
            },
            {
                'id': 'business',
                'name': 'Business',
                'price': 99.90,
                'period': 'mês',
                'features': [
                    'Análises ilimitadas',
                    'Análise premium',
                    'IA avançada',
                    'Suporte prioritário'
                ],
                'stripe_price_id': os.getenv('STRIPE_PRICE_BUSINESS')
            }
        ]
    })

@subscription.route('/subscribe', methods=['POST'])
@token_required
def create_subscription(current_user):
    """Cria uma nova assinatura"""
    try:
        plan_id = request.json.get('plan')
        if not plan_id:
            return jsonify({'error': 'Plano não especificado'}), 400

        # Configurar o preço baseado no plano
        if plan_id == 'premium':
            price_id = os.getenv('STRIPE_PRICE_PREMIUM')
        elif plan_id == 'business':
            price_id = os.getenv('STRIPE_PRICE_BUSINESS')
        else:
            return jsonify({'error': 'Plano inválido'}), 400

        # Criar ou recuperar o cliente no Stripe
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': str(current_user.id)}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Criar sessão de checkout
        success_url = request.host_url.rstrip('/') + '/subscription/success?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.host_url.rstrip('/') + '/subscription/cancel'
        
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(current_user.id),
                'plan': plan_id
            }
        )

        return jsonify({'checkout_url': checkout_session.url})

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao criar assinatura: {str(e)}'}), 500

@subscription.route('/webhook', methods=['POST'])
def webhook():
    """Processa webhooks do Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    elif event['type'] == 'customer.subscription.updated':
        subscription_object = event['data']['object']
        handle_subscription_updated(subscription_object)
    elif event['type'] == 'customer.subscription.deleted':
        subscription_object = event['data']['object']
        handle_subscription_deleted(subscription_object)

    return jsonify({'status': 'success'})

def handle_checkout_session(session):
    """Processa uma sessão de checkout completada"""
    user_id = session['metadata']['user_id']
    plan = session['metadata']['plan']
    user = User.query.get(user_id)
    
    if not user:
        return
    
    # Determinar número de análises e duração baseado no plano
    if plan == 'premium':
        analyses_limit = 20
    elif plan == 'business':
        analyses_limit = -1  # ilimitado
    else:
        analyses_limit = 3

    # Criar ou atualizar assinatura
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id)
    
    subscription.plan_type = plan
    subscription.remaining_analyses = analyses_limit
    subscription.expires_at = datetime.utcnow() + timedelta(days=30)
    subscription.stripe_subscription_id = session['subscription']
    
    db.session.add(subscription)
    db.session.commit()

def handle_subscription_updated(subscription_object):
    """Processa atualização de assinatura"""
    stripe_customer_id = subscription_object['customer']
    user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
    
    if not user:
        return
    
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if subscription:
        subscription.status = subscription_object['status']
        if subscription_object['status'] == 'active':
            subscription.expires_at = datetime.utcnow() + timedelta(days=30)
        db.session.commit()

def handle_subscription_deleted(subscription_object):
    """Processa cancelamento de assinatura"""
    stripe_customer_id = subscription_object['customer']
    user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
    
    if not user:
        return
    
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if subscription:
        subscription.plan_type = 'free'
        subscription.remaining_analyses = 3
        subscription.expires_at = datetime.utcnow() + timedelta(days=30)
        subscription.stripe_subscription_id = None
        db.session.commit()

@subscription.route('/success')
@token_required
def success(current_user):
    """Página de sucesso após assinatura"""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Sessão não encontrada'}), 400

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.metadata.get('user_id') != str(current_user.id):
            return jsonify({'error': 'Sessão inválida'}), 400

        return jsonify({
            'status': 'success',
            'message': 'Assinatura realizada com sucesso!'
        })
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400

@subscription.route('/cancel')
def cancel():
    """Página de cancelamento de assinatura"""
    return jsonify({
        'status': 'cancelled',
        'message': 'Assinatura cancelada'
    }) 