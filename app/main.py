"""
main.py — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.file_db import init_db
from app.routes import auth, expenses, income, savings, bills, analytics, categories

app = FastAPI(
    title="Smart Expense Tracker",
    description="A production-ready expense tracking API with analytics, file-based JSON storage, JWT auth, and CSV export.",
    version="1.0.0",
    contact={"name": "Muhammad Mamoon"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# API routers
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(income.router)
app.include_router(savings.router)
app.include_router(bills.router)
app.include_router(analytics.router)
app.include_router(categories.router)

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/", include_in_schema=False)
def serve_login():
    login_file = frontend_path / "login.html"
    if login_file.exists():
        return FileResponse(str(login_file))
    return {"message": "Smart Expense Tracker API", "docs": "/docs"}

@app.get("/app", include_in_schema=False)
@app.get("/app/{path:path}", include_in_schema=False)
def serve_app(path: str = ""):
    app_file = frontend_path / "dashboard.html"
    if app_file.exists():
        return FileResponse(str(app_file))
    return {"message": "Frontend not found"}

@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}
