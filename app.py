import os
from flask import Flask, request, render_template, jsonify, send_from_directory
from dotenv import load_dotenv
import openai
from models import db, User, Subscription, Analysis, SUBSCRIPTION_PLANS
from auth import auth, token_required
from subscription import subscription
import fitz  # PyMuPDF
from docx import Document
import werkzeug

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

# Initialize extensions
db.init_app(app)

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(subscription, url_prefix='/subscription')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx'}

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text).strip()
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def generate_feedback(cv_text, job_description):
    """Generate detailed feedback comparing CV with job requirements."""
    try:
        # Generate AI feedback using OpenAI
        prompt = f"""Analise este currículo para a vaga descrita e forneça um feedback detalhado em português.

Currículo:
{cv_text}

Descrição da Vaga:
{job_description}

Por favor, forneça uma análise estruturada incluindo:
1. Resumo da compatibilidade
2. Pontos fortes identificados
3. Áreas para melhoria
4. Sugestões específicas
5. Habilidades técnicas encontradas
6. Soft skills identificadas

Use emojis adequados para cada seção e mantenha o tom profissional e construtivo."""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        feedback = response.choices[0].message.content

        # Simular um score de compatibilidade baseado no comprimento do feedback
        similarity_score = min(len(feedback.split()) / 10, 100)  # 1 ponto para cada 10 palavras, max 100

        return {
            "similarity_score": similarity_score,
            "feedback": feedback,
            "using_ai": True
        }
        
    except Exception as e:
        return {
            "similarity_score": 0,
            "feedback": f"Erro ao analisar CV: {str(e)}",
            "using_ai": False
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
@token_required
def analyze(current_user):
    # Verificar se o usuário pode fazer análise
    if not current_user.subscription or not current_user.subscription.can_analyze():
        return jsonify({
            "error": "Limite de análises atingido ou assinatura expirada",
            "subscription_required": True
        }), 403
    
    cv_text = request.form.get('cv_text', '')
    job_description = request.form.get('job_description', '')
    cv_file = request.files.get('cv_file')
    
    # Se não houver texto do CV nem arquivo, retorna erro
    if not cv_text and not cv_file:
        return jsonify({"error": "CV não fornecido"}), 400
    
    if not job_description:
        return jsonify({"error": "Descrição da vaga não fornecida"}), 400
    
    try:
        # Se um arquivo foi enviado, processa-o
        if cv_file and cv_file.filename:
            if not allowed_file(cv_file.filename):
                return jsonify({"error": "Tipo de arquivo não suportado. Use PDF ou DOCX"}), 400
            
            # Salva o arquivo com um nome seguro
            filename = werkzeug.utils.secure_filename(cv_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cv_file.save(file_path)
            
            # Extrai o texto do arquivo
            if filename.endswith('.pdf'):
                cv_text = extract_text_from_pdf(file_path)
            else:  # .docx
                cv_text = extract_text_from_docx(file_path)
            
            # Remove o arquivo após extrair o texto
            os.remove(file_path)
            
            if not cv_text:
                return jsonify({"error": "Não foi possível extrair texto do arquivo"}), 400
        
        # Analyze CV
        result = generate_feedback(cv_text, job_description)
        
        # Save analysis
        analysis = Analysis(
            user_id=current_user.id,
            cv_filename=cv_file.filename if cv_file else "Texto direto",
            job_description=job_description,
            similarity_score=result['similarity_score'],
            feedback=result['feedback'],
            using_ai=result.get('using_ai', False)
        )
        db.session.add(analysis)
        
        # Update subscription usage
        current_user.subscription.use_analysis()
        db.session.commit()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Erro ao processar análise: {str(e)}"}), 500

@app.route('/history')
@token_required
def get_history(current_user):
    analyses = Analysis.query.filter_by(user_id=current_user.id)\
        .order_by(Analysis.created_at.desc())\
        .limit(10)\
        .all()
    
    return jsonify([{
        'id': a.id,
        'cv_filename': a.cv_filename,
        'similarity_score': a.similarity_score,
        'created_at': a.created_at.isoformat(),
        'using_ai': a.using_ai
    } for a in analyses])

if __name__ == '__main__':
    app.run(debug=True) 