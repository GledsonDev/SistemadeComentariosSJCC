# Sistema de Comentários com Moderação por IA

Este projeto é um sistema de comentários completo com backend em FastAPI e frontend em HTML/CSS/JavaScript. Ele permite que usuários se cadastrem, façam login, postem comentários e tenham seus comentários moderados por uma Inteligência Artificial (LLM) baseada em análise de sentimento.

## Funcionalidades

* **Cadastro de Usuário**: Novos usuários podem se registrar com nome, senha e uma foto de perfil opcional (upload de arquivo).
* **Login de Usuário**: Usuários registrados podem fazer login para interagir com o sistema.
* **Envio de Comentários**: Usuários logados podem postar comentários.
* **Moderação de Conteúdo por IA**:
    * Os comentários são analisados por um modelo de linguagem (LLM) da Hugging Face Transformers.
    * Atualmente, utiliza-se o modelo `nlptown/bert-base-multilingual-uncased-sentiment`.
    * Comentários classificados com sentimento muito negativo (1 ou 2 estrelas) são considerados "não aprovados".
* **Exibição de Comentários**:
    * Apenas comentários aprovados são exibidos publicamente na página principal.
    * A visualização dos comentários não requer login.
* **Armazenamento em Memória**: Dados de usuários e comentários são armazenados em memória (reiniciados com o servidor).
* **API Documentada**: A API backend possui documentação interativa via Swagger UI.

## Tech Stack

* **Backend**:
    * Python 3
    * FastAPI
    * Pydantic (para validação de dados)
    * Uvicorn (servidor ASGI)
* **Moderação IA**:
    * Hugging Face Transformers
    * Modelo: `nlptown/bert-base-multilingual-uncased-sentiment` (requer PyTorch ou TensorFlow)
* **Frontend**:
    * HTML5
    * CSS3
    * JavaScript

## Configuração e Instalação

### Pré-requisitos

* Python 3.8 ou superior
* pip (gerenciador de pacotes Python)

### Passos de Instalação

1.  **Clone o repositório (se aplicável) ou baixe os arquivos do projeto.**

2.  **Navegue até o diretório raiz do projeto.**

3.  **(Opcional, mas recomendado) Crie e ative um ambiente virtual Python:**
    ```bash
    python -m venv venv
    # No Windows:
    # venv\Scripts\activate
    # No macOS/Linux:
    # source venv/bin/activate
    ```

4.  **Instale as dependências Python:**
    ```bash
    pip install fastapi uvicorn[standard] pydantic python-multipart transformers torch
    ```
    *Nota: `torch` instala o PyTorch. Se preferir TensorFlow, instale `tensorflow` em vez de `torch`.*

5.  **Estrutura de diretórios**: Certifique-se de que a estrutura de pastas `frontend/static/user_images/` exista. O backend tentará criá-la, mas você pode criar manualmente se necessário.

## Executando a Aplicação

1.  **Inicie o servidor backend FastAPI:**
    No diretório raiz do projeto, execute:
    ```bash
    uvicorn backend.main:app --reload
    ```
    * `--reload` faz o servidor reiniciar automaticamente após alterações no código (ótimo para desenvolvimento).

2.  **Acesse o Frontend:**
    * Como os endpoints que serviam as páginas HTML diretamente do FastAPI foram removidos para simplificar a documentação do Swagger, você precisará acessar o frontend de outra forma.
    * **Para desenvolvimento local**: Navegue até a pasta `frontend/templates/` e abra o arquivo `index.html` diretamente no seu navegador web (ex: `file:///caminho/para/seu_projeto/frontend/templates/index.html`).
        * A partir do `index.html`, você poderá navegar para as páginas de login e cadastro.
    * **Para produção**: Você normalmente serviria esses arquivos estáticos (HTML, CSS, JS) através de um servidor web como Nginx ou similar.

3.  **Acesse a Documentação da API (Swagger UI):**
    Com o servidor backend rodando, abra no seu navegador:
    `http://127.0.0.1:8000/docs`

## Endpoints da API

A API RESTful fornece os seguintes endpoints principais (detalhes completos na Swagger UI):

* `POST /api/v1/register`: Registra um novo usuário.
* `POST /api/v1/login`: Autentica um usuário.
* `POST /api/v1/comments`: Submete um novo comentário (requer autenticação).
* `GET /api/v1/comments`: Lista todos os comentários aprovados.
* `GET /api/v1/comments/all`: Lista todos os comentários no sistema (aprovados e não aprovados).

## Moderação de Comentários

A moderação é feita pela função `analisar_comentario` no arquivo `backend/moderation.py`.
* Ela usa o modelo `nlptown/bert-base-multilingual-uncased-sentiment` da Hugging Face.
* Comentários classificados pelo modelo com sentimento de "1 star" ou "2 stars" são considerados inadequados e não são aprovados.
* O modelo é baixado automaticamente na primeira execução se não estiver no cache local do `transformers`.

---