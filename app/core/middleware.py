from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def register_middleware(app: FastAPI) -> None:
    settings = get_settings()
    
    # Define allowed origins - combine settings cors_origins with common patterns
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://hostelproject-eta.vercel.app",
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ]
    
    # Also include any origins from settings
    if settings.cors_origins:
        allowed_origins.extend(settings.cors_origins)
    
    # Remove duplicates while preserving order
    unique_origins = []
    for origin in allowed_origins:
        if origin not in unique_origins:
            unique_origins.append(origin)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=unique_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )