# Chef Agent API

A FastAPI-based service that generates recipes based on user input (text or images) using LangChain and LangGraph agents.

## Features

- 🤖 AI-powered recipe generation from text or image inputs
- 🔐 Auth0 authentication
- 💬 Streaming chat responses (Server-Sent Events)
- 🗄️ PostgreSQL persistence for conversation threads and user data
- 🖼️ Multimodal support (text + images)
- 🌍 Multi-language support
- 📦 Clean architecture with separation of concerns

## Tech Stack

- **FastAPI** - Modern web framework
- **LangChain** - LLM orchestration and tooling
- **LangGraph** - Agent state management with PostgreSQL checkpointing
- **PostgreSQL** - Database (checkpointing + user data)
- **Auth0** - Authentication and authorization
- **uv** - Fast Python package manager
- **Docker & Docker Compose** - Containerization
- **Alembic** - Database migrations

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- uv (Python package manager)
- PostgreSQL 15+ (via Docker)

## Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd chef_agent_api
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**

   ```bash
   docker compose up --build
   ```

4. **Run database migrations**
   ```bash
   docker compose exec api uv run alembic upgrade head
   ```

The API will be available at `http://localhost:8000`

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=db
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db:5432/db

# Auth0
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_AUDIENCE=your_api_audience
AUTH0_CLIENT_ID=your_client_id
AUTH0_MGMT_CLIENT_ID=your_mgmt_client_id
AUTH0_MGMT_CLIENT_SECRET=your_mgmt_client_secret
AUTH0_MGMT_AUDIENCE=your_mgmt_audience

# OpenAI
OPENAI_API_KEY=your_openai_key

# Tavily Search API
TAVILY_API_KEY=your_tavily_key

# CORS (optional, comma-separated)
BACKENDS_CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Timezone (optional)
TIMEZONE=America/Sao_Paulo
```

## API Endpoints

### Chat

**POST** `/api/v1/chat/stream`

- Stream recipe generation responses
- **Authentication**: Required (Bearer token)
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `thread_id` (form, required): Conversation thread identifier
  - `message` (form, required): Text message from user
  - `image` (file, optional): Image file (jpeg, png, webp, gif)
  - `user_language` (form, optional): Preferred response language (default: "English")
- **Response**: Server-Sent Events (SSE) stream with `text/event-stream` content type

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "thread_id=abc-123" \
  -F "message=What can I cook with these ingredients?" \
  -F "image=@photo.jpg" \
  -F "user_language=English"
```

### User

**GET** `/api/v1/user/me`

- Get current authenticated user profile
- **Authentication**: Required

**PATCH** `/api/v1/user/me`

- Update current user profile
- **Authentication**: Required

## API Documentation

Once running, visit:

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Project Structure

```
chef_agent_api/
├── app/
│   ├── agents/
│   │   └── chef_agent/          # LangChain agent implementation
│   │       ├── agent.py          # Agent definition
│   │       ├── checkpointer.py   # PostgreSQL checkpointing
│   │       ├── middlewares.py    # Agent middlewares
│   │       ├── prompt.py         # System prompts
│   │       ├── schemas.py        # Agent context schemas
│   │       └── tools/            # Agent tools (web search, etc.)
│   ├── api/
│   │   └── v1/
│   │       ├── routers/          # API route handlers
│   │       └── dependencies/     # FastAPI dependencies (auth, db)
│   ├── core/                     # Configuration and settings
│   ├── db_config/                # Database session management
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business logic layer
│   │   └── chat_service.py       # Chat service
│   └── main.py                   # FastAPI application
├── alembic/                      # Database migrations
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Container definition
├── pyproject.toml                # Dependencies (uv)
└── README.md                     # This file
```

## Development

### Running Locally (without Docker)

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Set up environment**

   ```bash
   export $(cat .env | xargs)
   ```

3. **Run the application**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Database Migrations

```bash
# Create a new migration
docker compose exec api uv run alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec api uv run alembic upgrade head

# Check current migration status
docker compose exec api uv run alembic current
```

### Adding Dependencies

```bash
# Add a new package
uv add package-name

# Add with extras
uv add "package[extras]"
```

### Docker Commands

```bash
# Build and start services
docker compose up --build

# Start in detached mode
docker compose up -d

# View logs
docker compose logs -f api

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Architecture

The project follows **clean architecture** principles:

- **API Layer** (`app/api/`): Thin route handlers, HTTP concerns only
- **Service Layer** (`app/services/`): Business logic and orchestration
- **Agent Layer** (`app/agents/`): LangChain/LangGraph agent implementations
- **Data Layer** (`app/models/`, `app/db_config/`): Database models and sessions
- **Schemas** (`app/schemas/`): Data validation and serialization

## Authentication

The API uses Auth0 for authentication. To authenticate:

1. Get an access token from Auth0
2. Include it in the `Authorization` header: `Bearer <token>`
3. The API validates the token and extracts user information
