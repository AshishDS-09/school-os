# backend/app/main.py

from fastapi import FastAPI

app = FastAPI(
    title="School OS API",
    description="AI-Powered School Operating System",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "School OS API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}