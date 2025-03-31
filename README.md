# 📄 Analisador de CV

Um analisador de currículos que compara seu CV com descrições de vagas e fornece feedback personalizado.

## 🚀 Funcionalidades

- ✨ Upload de CV em formato PDF ou DOCX
- 📊 Análise de compatibilidade com a vaga
- 🎯 Identificação de palavras-chave e habilidades
- 💡 Sugestões personalizadas de melhorias
- 📈 Score de compatibilidade
- 🔍 Análise detalhada de requisitos

## 🛠️ Tecnologias Utilizadas

- Python 3.8+
- Flask (Framework web)
- PyMuPDF (Extração de texto de PDFs)
- python-docx (Leitura de arquivos Word)
- FuzzyWuzzy (Análise de similaridade)

## ⚙️ Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git

## 📥 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/agostinhomarcia/analyzer.git
cd analyzer
```

2. Configure o ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:

```bash
# Copie o arquivo de exemplo
cp .env.example .env
# Edite o arquivo .env e adicione suas configurações
```

## 🚀 Como Usar

1. Inicie o servidor:

```bash
python app.py
```

2. Acesse a aplicação:

- Abra seu navegador
- Acesse `http://127.0.0.1:5000`

3. Use a interface para:

- Fazer upload do seu CV (PDF ou DOCX)
- Colar a descrição da vaga
- Receber análise detalhada

## 📊 Análise Fornecida

O sistema analisa:

- 💪 Pontos fortes do seu CV
- 📋 Requisitos atendidos e faltantes
- ⏳ Experiência requerida
- 📚 Formação acadêmica
- 💡 Recomendações personalizadas

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Estrutura do Projeto

```
analyzer/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências do projeto
├── .env.example       # Exemplo de configuração
├── .gitignore        # Arquivos ignorados pelo git
├── README.md         # Este arquivo
└── templates/        # Templates HTML
    └── index.html    # Interface principal
```

## ⚠️ Notas Importantes

- Mantenha seu arquivo `.env` seguro e nunca o compartilhe
- A pasta `uploads` é criada automaticamente para arquivos temporários
- Os arquivos enviados são deletados após a análise
- O sistema funciona offline, sem depender de APIs externas

## 👩‍💻 Autor

Márcia Agostinho

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
