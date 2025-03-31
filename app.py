import os
from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
from docx import Document
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
import re
from collections import defaultdict

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Predefined skills and categories
SKILL_CATEGORIES = {
    'programming_languages': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php',
        'swift', 'kotlin', 'go', 'rust', 'scala', 'perl', 'r', 'matlab'
    ],
    'web_technologies': [
        'html', 'css', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
        'spring', 'asp.net', 'express', 'jquery', 'bootstrap', 'tailwind',
        'graphql', 'rest', 'api', 'apis', 'rest api', 'restful', 'websocket'
    ],
    'databases': [
        'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis',
        'elasticsearch', 'cassandra', 'dynamodb', 'firebase'
    ],
    'cloud_platforms': [
        'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
        'kubernetes', 'docker', 'terraform', 'jenkins'
    ],
    'soft_skills': [
        'liderança', 'comunicação', 'trabalho em equipe', 'proativo',
        'resolução de problemas', 'organização', 'gestão de tempo',
        'adaptabilidade', 'criatividade', 'inovação', 'autonomia',
        'proatividade', 'colaboração', 'aprendizado contínuo'
    ],
    'methodologies': [
        'agile', 'scrum', 'kanban', 'lean', 'waterfall', 'tdd', 'bdd',
        'devops', 'ci/cd', 'xp', 'ágil'
    ],
    'security': [
        'autenticação', 'autorização', 'oauth', 'jwt', 'segurança',
        'criptografia', 'ssl', 'https', 'firewall', 'pentest'
    ],
    'quality': [
        'qualidade de código', 'code review', 'testes unitários',
        'testes de integração', 'testes automatizados', 'qa',
        'garantia de qualidade', 'debugging', 'performance'
    ]
}

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file."""
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def find_skills(text):
    """Find skills in text and categorize them."""
    text = text.lower()
    found_skills = defaultdict(list)
    
    for category, skills in SKILL_CATEGORIES.items():
        for skill in skills:
            if skill.lower() in text:
                found_skills[category].append(skill)
    
    return found_skills

def extract_requirements(job_description):
    """Extract key requirements from job description."""
    text = job_description.lower()
    requirements = {
        'required_skills': [],
        'preferred_skills': [],
        'experience_years': None,
        'education': []
    }
    
    # Find required skills - first try with explicit sections
    required_patterns = [
        r'requisitos:.*?(?=\n\n|\Z)',
        r'necessário:.*?(?=\n\n|\Z)',
        r'obrigatório:.*?(?=\n\n|\Z)',
        r'required:.*?(?=\n\n|\Z)'
    ]
    
    skills_found = False
    for pattern in required_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            for match in matches:
                skills = re.findall(r'[\w\+\#]+(?:\s+[\w\+\#]+)*', match)
                requirements['required_skills'].extend(skills)
                skills_found = True
    
    # If no explicit sections found, extract skills from the entire text
    if not skills_found:
        # Split text into words and phrases
        words = re.findall(r'[\w\+\#]+(?:\s+[\w\+\#]+)*', text)
        
        # Add common technical terms and skills
        for word in words:
            word = word.strip().lower()
            # Check if word is in any of our predefined skills
            for category_skills in SKILL_CATEGORIES.values():
                if word in [skill.lower() for skill in category_skills]:
                    if word not in requirements['required_skills']:
                        requirements['required_skills'].append(word)
    
    # Find years of experience
    experience_patterns = [
        r'(\d+)[\s-]*anos de experiência',
        r'experiência de (\d+)[\s-]*anos',
        r'(\d+)[\s-]*years of experience'
    ]
    
    for pattern in experience_patterns:
        match = re.search(pattern, text)
        if match:
            requirements['experience_years'] = int(match.group(1))
            break
    
    # Find education requirements
    education_patterns = [
        r'graduação em .*?(?=\n|\Z)',
        r'formação em .*?(?=\n|\Z)',
        r'bacharel em .*?(?=\n|\Z)',
        r'degree in .*?(?=\n|\Z)'
    ]
    
    for pattern in education_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        requirements['education'].extend(matches)
    
    return requirements

def generate_feedback(cv_text, job_description):
    """Generate detailed feedback comparing CV with job requirements."""
    cv_skills = find_skills(cv_text)
    job_requirements = extract_requirements(job_description)
    
    # Initialize missing_skills
    missing_skills = []
    
    # Calculate basic similarity score
    similarity_score = fuzz.token_set_ratio(cv_text, job_description)
    
    # Analyze matches and gaps
    feedback = []
    feedback.append("📊 Análise do seu CV:\n")
    
    # Skills found in CV
    feedback.append("\n💪 Pontos Fortes:")
    for category, skills in cv_skills.items():
        if skills:
            category_name = category.replace('_', ' ').title()
            feedback.append(f"\n• {category_name}: {', '.join(skills)}")
    
    # Required skills analysis
    if job_requirements['required_skills']:
        feedback.append("\n\n📋 Requisitos da Vaga:")
        matched_skills = []
        missing_skills = []  # Reset missing_skills here
        
        for skill in job_requirements['required_skills']:
            skill_found = False
            for category_skills in cv_skills.values():
                if skill in [s.lower() for s in category_skills]:
                    matched_skills.append(skill)
                    skill_found = True
                    break
            if not skill_found:
                missing_skills.append(skill)
        
        if matched_skills:
            feedback.append(f"\n✅ Requisitos Atendidos: {', '.join(matched_skills)}")
        if missing_skills:
            feedback.append(f"\n❌ Requisitos Faltantes: {', '.join(missing_skills)}")
    
    # Experience analysis
    if job_requirements['experience_years']:
        feedback.append(f"\n\n⏳ Experiência Requerida: {job_requirements['experience_years']} anos")
    
    # Education analysis
    if job_requirements['education']:
        feedback.append("\n\n📚 Formação Acadêmica Requerida:")
        for edu in job_requirements['education']:
            feedback.append(f"\n• {edu}")
    
    # Recommendations
    feedback.append("\n\n💡 Recomendações:")
    if similarity_score < 60:
        feedback.append("\n• Considere adicionar mais palavras-chave específicas da vaga")
        feedback.append("\n• Detalhe melhor suas experiências relacionadas aos requisitos")
    if missing_skills:  # Now missing_skills is always defined
        feedback.append("\n• Destaque projetos ou experiências relacionados aos requisitos faltantes")
        feedback.append("\n• Se possui conhecimento em alguma das habilidades faltantes, adicione-as ao CV")
    
    feedback.append("\n\n📝 Dicas Gerais:")
    feedback.append("\n• Mantenha o CV conciso e objetivo")
    feedback.append("\n• Use bullets points para listar realizações")
    feedback.append("\n• Quantifique resultados quando possível")
    feedback.append("\n• Personalize o CV para cada vaga")
    
    return {
        "similarity_score": similarity_score,
        "feedback": "\n".join(feedback)
    }

def analyze_cv(cv_text, job_description):
    """Analyze CV against job description and generate feedback."""
    try:
        result = generate_feedback(cv_text, job_description)
        return result
    except Exception as e:
        return {
            "similarity_score": 0,
            "feedback": f"Erro ao analisar CV: {str(e)}"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'cv_file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['cv_file']
    job_description = request.form.get('job_description', '')
    
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    if not job_description:
        return jsonify({"error": "Descrição da vaga não fornecida"}), 400
    
    # Save uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    try:
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            cv_text = extract_text_from_pdf(file_path)
        elif file.filename.lower().endswith('.docx'):
            cv_text = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": "Formato de arquivo não suportado"}), 400
        
        # Analyze CV
        result = analyze_cv(cv_text, job_description)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify(result)
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Erro ao processar arquivo: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True) 