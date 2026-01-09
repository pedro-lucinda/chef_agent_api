
# Chef Agent API

A FastAPI-based service that generates recipes based on user input (text or images) using LangChain and LangGraph agents.

## Features

- 🤖 AI-powered recipe generation from text or image inputs
- 🔐 Auth0 authentication
- 💬 Streaming chat responses
- 🗄️ PostgreSQL persistence for conversation threads
- 🖼️ Multimodal support (text + images)
- 🌍 Multi-language support

## Tech Stack

- **FastAPI** - Web framework
- **LangChain** - LLM orchestration
- **LangGraph** - Agent state management
- **PostgreSQL** - Database (checkpointing + user data)
- **Auth0** - Authentication
- **uv** - Package management
- **Docker** - Containerization

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- uv (Python package manager)
- PostgreSQL 15+

## Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd chef_agent_api
   ```

2. **Install dependencies**

   ```bash
   uv sync
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Required environment variables**

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

   # Tavily Search
   TAVILY_API_KEY=your_tavily_key
   ```

5. **Run database migrations**
   ```bash
   docker compose exec api uv run alembic upgrade head
   ```

## Running the Application

### Using Docker Compose (Recommended)

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`

### Local Development

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Chat

**POST** `/api/v1/chat/stream`

- Stream recipe generation responses
- **Authentication**: Required (Bearer token)
- **Parameters**:
  - `thread_id` (form): Conversation thread identifier
  - `message` (form): Text message
  - `image` (file, optional): Image file
  - `user_language` (form, optional): Preferred language (default: "English")
- **Response**: Server-Sent Events (SSE) stream

### User

**GET** `/api/v1/user/me`

- Get current user profile
- **Authentication**: Required

**PATCH** `/api/v1/user/me`

- Update current user profile
- **Authentication**: Required

## API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
chef_agent_api/
├── app/
│   ├── api/v1/routers/     # API endpoints
│   ├── core/               # Configuration
│   ├── db_config/          # Database setup
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic
│       └── agents/         # LangChain agents
├── alembic/                # Database migrations
├── docker-compose.yml      # Docker services
├── Dockerfile              # Container definition
└── pyproject.toml          # Dependencies
```

## Development

### Running Migrations

```bash
# Create migration
docker compose exec api uv run alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec api uv run alembic upgrade head
```

### Adding Dependencies

```bash
uv add package-name
```

## License

[Add your license here]
