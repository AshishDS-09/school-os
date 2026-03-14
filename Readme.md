# School OS — AI-Powered School Operating System

A SaaS platform for schools with 10 AI agents for academic monitoring,
attendance prediction, fee collection, parent communication, and more.

## Tech Stack
- **Frontend**: Next.js 14, ShadCN UI, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI**: LangChain, LangGraph, OpenAI GPT-4o
- **Infra**: Docker, Redis, Celery, Supabase

## Local Development Setup

### Prerequisites
- Docker Desktop for Windows
- Node.js 20+
- Python 3.11+

### Run locally
```bash
# 1. Clone the repo
git clone https://github.com/yourusername/school-os.git
cd school-os

# 2. Copy env template and fill in your keys
cp .env.example backend/.env

# 3. Start all services
docker compose up -d

# 4. Verify all 8 services are running
docker ps
```

### Service URLs
| Service | URL |
|---|---|
| Backend API | http://localhost:8000/docs |
| Database browser | http://localhost:8080 |
| Celery monitor | http://localhost:5555 |

## Build Phases
See the full guide document for all 11 build phases.