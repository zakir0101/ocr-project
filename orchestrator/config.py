"""
Orchestrator Configuration

Configuration settings for the OCR orchestrator server.
"""

import os
from typing import Dict, Any

# Backend server configurations
BACKEND_CONFIGS = {
    "deepseek-ocr": {
        "url": "http://localhost:5000",
        "health_endpoint": "/health",
        "image_ocr_endpoint": "/ocr/image",
        "pdf_ocr_endpoint": "/ocr/pdf",
        "description": "DeepSeek OCR Backend",
        "gpu": "RTX 3090 #1"
    },
    "mineru": {
        "url": "http://localhost:5001",
        "health_endpoint": "/health",
        "image_ocr_endpoint": "/ocr/image",
        "pdf_ocr_endpoint": "/ocr/pdf",
        "description": "Mineru Backend",
        "gpu": "RTX 3090 #2"
    }
}

# Request timeout settings (in seconds)
TIMEOUT_CONFIG = {
    "ocr_request": 120,  # OCR processing timeout
    "health_check": 10,   # Health check timeout
    "connection": 5       # Connection timeout
}

# Health monitoring settings
HEALTH_CONFIG = {
    "check_interval": 30,  # Health check interval in seconds
    "failure_threshold": 3,  # Consecutive failures before marking unhealthy
    "success_threshold": 2   # Consecutive successes before marking healthy
}

# CORS configuration for web client
CORS_CONFIG = {
    "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}

# Server configuration
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": False,
    "threaded": True
}

# Logging configuration
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/orchestrator.log"
}

def get_backend_url(backend_name: str, endpoint: str) -> str:
    """
    Get full URL for a backend endpoint.

    Args:
        backend_name: Name of the backend ("deepseek-ocr" or "mineru")
        endpoint: The endpoint path (e.g., "/ocr/image")

    Returns:
        Full URL for the backend endpoint
    """
    if backend_name not in BACKEND_CONFIGS:
        raise ValueError(f"Unknown backend: {backend_name}")

    base_url = BACKEND_CONFIGS[backend_name]["url"]
    return f"{base_url}{endpoint}"

def get_backend_health_url(backend_name: str) -> str:
    """Get health check URL for a backend."""
    return get_backend_url(backend_name, "/health")

def get_backend_image_ocr_url(backend_name: str) -> str:
    """Get image OCR URL for a backend."""
    return get_backend_url(backend_name, "/ocr/image")

def get_backend_pdf_ocr_url(backend_name: str) -> str:
    """Get PDF OCR URL for a backend."""
    return get_backend_url(backend_name, "/ocr/pdf")