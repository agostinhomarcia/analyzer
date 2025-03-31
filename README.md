# Analisador de CV

Este projeto é um analisador de currículos que compara o CV do usuário com uma descrição de vaga e fornece feedback personalizado.

## Funcionalidades

- Extração de texto de arquivos PDF e DOCX
- Análise de palavras-chave e comparação com descrição da vaga
- Geração de feedback personalizado usando IA
- Interface web para upload de arquivos

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure sua chave API da OpenAI:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione sua chave API: `OPENAI_API_KEY=sua_chave_aqui`

## Uso

1. Execute o servidor Flask:

```bash
python app.py
```

2. Acesse http://localhost:5000 no seu navegador
3. Faça upload do seu CV e insira a descrição da vaga
4. Receba feedback personalizado sobre seu CV
