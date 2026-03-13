"""Very small admin auth for MVP (static bearer token)."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import AdminUser

DEFAULT_ADMIN_TOKEN = "dev-admin-token"


def _admin_token() -> str:
    # Environment:
    #  - ADMIN_TOKEN: override token for deployments
    return os.getenv("ADMIN_TOKEN", DEFAULT_ADMIN_TOKEN)


# PUBLIC_INTERFACE
def require_admin(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> AdminUser:
    """
    FastAPI dependency to require admin access.

    MVP behavior:
      - Expect `Authorization: Bearer <ADMIN_TOKEN>`
      - Also verifies that at least one admin user exists.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != _admin_token():
        raise HTTPException(status_code=403, detail="Invalid admin token")

    admin = db.query(AdminUser).first()
    if not admin:
        raise HTTPException(status_code=500, detail="Admin not initialized")
    return admin
