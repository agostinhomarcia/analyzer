import os
from flask import Flask
from models import db

# Ensure instance directory exists
os.makedirs('instance', exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()
    print("Banco de dados criado com sucesso!") 