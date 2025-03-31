import requests
import json

class AIAnalyzer:
    def __init__(self, model="mistral"):
        self.base_url = "http://localhost:11434/api"
        self.model = model
        
    def _generate_prompt(self, cv_text, job_description):
        return f"""Analise este currículo para a vaga descrita e forneça um feedback detalhado.

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

Mantenha o tom profissional e construtivo."""

    def analyze(self, cv_text, job_description):
        """Analisa o CV usando o modelo Ollama."""
        try:
            prompt = self._generate_prompt(cv_text, job_description)
            
            # Configuração da requisição para o Ollama
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "analysis": result["response"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro na API do Ollama: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao analisar com IA: {str(e)}"
            }
    
    def is_available(self):
        """Verifica se o serviço Ollama está disponível."""
        try:
            response = requests.get(f"{self.base_url}/tags")
            return response.status_code == 200
        except:
            return False 