# Sistema de Comentários com Moderação por IA

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-blue?logo=fastapi)
![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Transformers-yellow)

Um sistema de comentários completo com backend em FastAPI e frontend em HTML/CSS/JS, que utiliza um modelo de linguagem (LLM) para realizar moderação de conteúdo em tempo real através de análise de sentimento.

---

## ✨ Funcionalidades Principais

- **👤 Gestão de Usuários**: Sistema completo de cadastro com foto de perfil e login.
- **✍️ Envio de Comentários**: Usuários autenticados podem submeter novos comentários.
- **🤖 Moderação por IA**: Cada comentário é analisado por um modelo de linguagem da Hugging Face para determinar seu sentimento.
- **👍 Aprovação Automática**: Comentários com sentimento positivo/neutro são aprovados e exibidos publicamente. Comentários muito negativos são retidos.
- **📖 Visualização Pública**: Qualquer visitante pode ver os comentários aprovados, incentivando a leitura e o engajamento.
- **📄 API Documentada**: A API do backend é totalmente documentada e interativa com Swagger UI.

---

## 🧠 Como Funciona a Moderação por IA

A moderação de conteúdo é o coração deste projeto.

1. **Modelo Utilizado**: Usamos o modelo `nlptown/bert-base-multilingual-uncased-sentiment` da biblioteca `transformers` da Hugging Face.
2. **Análise de Sentimento**: Quando um comentário é enviado, a função `analisar_comentario` (em `backend/moderation.py`) o processa.
3. **Classificação**: O modelo classifica o sentimento do texto em uma escala de 1 a 5 estrelas.
4. **Tomada de Decisão**: Comentários classificados com **1 ou 2 estrelas** (sentimento muito negativo) são marcados como "não aprovados" e não aparecem publicamente. Os demais são aprovados.

---

## 🛠️ Tecnologias Utilizadas

**Backend**:
- Python 3
- FastAPI (para a API RESTful)
- Pydantic (para validação de dados)
- Uvicorn (servidor ASGI)

**Inteligência Artificial**:
- Hugging Face Transformers
- PyTorch (ou TensorFlow)

**Frontend**:
- HTML5
- CSS3
- JavaScript (Puro)

---

## 🚀 Configuração e Execução

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 1. Preparando o Ambiente

```bash
# Crie e ative um ambiente virtual
python -m venv venv

# No macOS/Linux:
source venv/bin/activate

# No Windows:
venv\Scripts\activate
```

### 2. Instalando as Dependências

Instale tudo com um único comando no terminal:

```bash
pip install -r requirements.txt
```

### 3. Executando o Projeto

**Terminal: Inicie o Backend (API)**

```bash
uvicorn backend.main:app --reload
```

O servidor da API estará rodando em:  
👉 http://127.0.0.1:8000

---

### 4. Acessando a Documentação da API

Com o backend rodando, acesse a documentação interativa (Swagger UI) em:  
👉 http://127.0.0.1:8000/docs

---

## 📌 Endpoints da API

- `POST /api/v1/register`: Registra um novo usuário.
- `POST /api/v1/login`: Autentica um usuário e retorna um token.
- `POST /api/v1/comments`: Submete um novo comentário (requer autenticação).
- `GET /api/v1/comments`: Lista todos os comentários aprovados.
- `GET /api/v1/comments/all`: Lista todos os comentários do sistema (aprovados e não aprovados).