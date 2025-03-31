from flask import Blueprint, request, jsonify
from models import db, User, Subscription, SUBSCRIPTION_PLANS
from auth import token_required
from datetime import datetime, timedelta
import stripe
import os

subscription = Blueprint('subscription', __name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@subscription.route('/plans')
def get_plans():
    return jsonify(SUBSCRIPTION_PLANS)

@subscription.route('/subscribe', methods=['POST'])
@token_required
def subscribe(current_user):
    data = request.get_json()
    plan_type = data.get('plan')
    
    if not plan_type or plan_type not in SUBSCRIPTION_PLANS:
        return jsonify({'message': 'Plano inválido'}), 400
    
    try:
        # Criar sessão de checkout do Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'unit_amount': int(SUBSCRIPTION_PLANS[plan_type]['price'] * 100),
                    'product_data': {
                        'name': f"Plano {SUBSCRIPTION_PLANS[plan_type]['name']}",
                        'description': 'Assinatura mensal'
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription/cancel',
            client_reference_id=str(current_user.id),
            metadata={
                'plan_type': plan_type
            }
        )
        
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        return jsonify({'message': f'Erro ao criar assinatura: {str(e)}'}), 500

@subscription.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        return jsonify({'message': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'message': 'Invalid signature'}), 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = int(session['client_reference_id'])
        plan_type = session['metadata']['plan_type']
        
        user = User.query.get(user_id)
        if user:
            # Update or create subscription
            if user.subscription:
                subscription = user.subscription
            else:
                subscription = Subscription(user_id=user.id)
            
            subscription.plan_type = plan_type
            subscription.analyses_remaining = SUBSCRIPTION_PLANS[plan_type]['analyses_per_month']
            subscription.expires_at = datetime.utcnow() + timedelta(days=30)
            
            db.session.add(subscription)
            db.session.commit()
    
    return jsonify({'status': 'success'})

@subscription.route('/success')
@token_required
def success(current_user):
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'message': 'Sessão não encontrada'}), 400
        
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.client_reference_id != str(current_user.id):
            return jsonify({'message': 'Sessão inválida'}), 400
            
        return jsonify({
            'message': 'Assinatura realizada com sucesso',
            'plan': session.metadata.plan_type
        })
        
    except Exception as e:
        return jsonify({'message': f'Erro ao verificar assinatura: {str(e)}'}), 500

@subscription.route('/cancel')
@token_required
def cancel(current_user):
    return jsonify({'message': 'Assinatura cancelada'}) 