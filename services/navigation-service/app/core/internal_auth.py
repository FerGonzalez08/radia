from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_internal_key(x_internal_service_key: str = Header(...)):
    if x_internal_service_key != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid internal service key")
