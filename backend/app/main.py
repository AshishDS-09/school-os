# # backend/app/main.py    for starting the FastAPI server. All API endpoints are registered here.

# from fastapi import FastAPI

# app = FastAPI(
#     title="School OS API",
#     description="AI-Powered School Operating System",
#     version="1.0.0"
# )

# @app.get("/")
# def root():
#     return {"status": "School OS API is running", "version": "1.0.0"}

# @app.get("/health")
# def health():
#     return {"status": "healthy"}
# backend/app/main.py


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# backend/app/main.py  — updated imports and router registration

from app.api import (
    auth, students, attendance, marks,
    fees, notifications, agent_logs, gemini,
    incidents, leads, classes, users
)
from app.api import teacher_tools
# backend/app/main.py  — add these lines
from app.api import billing


from app.core.config import settings


app = FastAPI(
    title="School OS API",
    description="AI-Powered School Operating System — Backend API",
    version="2.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc UI
)

# ── CORS — allow frontend (localhost:3000) to call the API ──────────
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",   # Next.js dev server
#         "http://localhost:3001",
#         "https://yourdomain.com",  # production domain
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routers ────────────────────────────────────────────
app.include_router(billing.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(classes.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(marks.router)
app.include_router(fees.router)
app.include_router(notifications.router)
app.include_router(agent_logs.router)
app.include_router(gemini.router, prefix="/ai", tags=["Gemini AI"])
# add these two lines alongside the other include_router calls:
app.include_router(incidents.router)
app.include_router(leads.router)
app.include_router(teacher_tools.router)


# ── Health check endpoints ──────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "School OS API running", "version": "2.0.0", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
