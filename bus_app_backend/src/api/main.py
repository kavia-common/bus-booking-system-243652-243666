"""
Bus Booking MVP FastAPI application.

Provides:
- Public APIs for browsing routes/trips, viewing seat availability, and booking.
- Admin APIs (MVP) for managing routes/buses/trips.

Environment variables (request orchestrator to set in .env if needed):
- SQLITE_DB: absolute path to the SQLite database file.
- ADMIN_TOKEN: bearer token for admin endpoints (default: dev-admin-token).

Admin usage (MVP):
- POST /api/admin/login with {"username":"admin","password":"admin"} to get token
- Then call admin endpoints with header: Authorization: Bearer <token>
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.db import Base, engine
from src.api.routers import admin_router, public_router

openapi_tags = [
    {"name": "Public", "description": "Trip search, seat availability, booking & confirmation."},
    {"name": "Admin", "description": "MVP admin CRUD for routes/buses/trips (bearer token)."},
]

app = FastAPI(
    title="Bus Booking MVP API",
    description="Retro-themed bus booking MVP backend: trips, seats, bookings, and simple admin management.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: open CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup_create_tables() -> None:
    """
    Ensure tables exist on startup.

    Note: For a real system, use migrations. For MVP, we create from ORM models.
    """
    Base.metadata.create_all(bind=engine)


@app.get("/", summary="Health check", operation_id="health_check")
def health_check():
    """Simple health check endpoint."""
    return {"message": "Healthy"}


app.include_router(public_router)
app.include_router(admin_router)
