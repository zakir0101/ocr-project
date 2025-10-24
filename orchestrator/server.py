"""
OCR Orchestrator Server

Main orchestrator server that routes client requests to the appropriate backend
and provides unified API responses.
"""

import os
import sys
import time
import logging
import requests
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from flask_cors import CORS
from config import (
    BACKEND_CONFIGS, TIMEOUT_CONFIG, CORS_CONFIG, SERVER_CONFIG,
    get_backend_image_ocr_url, get_backend_pdf_ocr_url, get_backend_health_url
)
from shared.api_contract import create_unified_response

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for web client
CORS(app, origins=CORS_CONFIG["origins"],
     methods=CORS_CONFIG["methods"],
     allow_headers=CORS_CONFIG["allow_headers"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Backend health status tracking
backend_status = {
    "deepseek-ocr": {
        "healthy": False,
        "last_check": 0,
        "consecutive_failures": 0,
        "consecutive_successes": 0
    },
    "mineru": {
        "healthy": False,
        "last_check": 0,
        "consecutive_failures": 0,
        "consecutive_successes": 0
    }
}


def check_backend_health(backend_name: str) -> bool:
    """
    Check the health status of a backend.

    Args:
        backend_name: Name of the backend to check

    Returns:
        True if backend is healthy, False otherwise
    """
    try:
        health_url = get_backend_health_url(backend_name)
        response = requests.get(health_url, timeout=TIMEOUT_CONFIG["health_check"])

        if response.status_code == 200:
            health_data = response.json()
            return health_data.get("status") == "healthy" and health_data.get("model_loaded", False)

        return False

    except Exception as e:
        logger.warning(f"Health check failed for {backend_name}: {e}")
        return False


def update_backend_health_status():
    """Update health status for all backends."""
    current_time = time.time()

    for backend_name in BACKEND_CONFIGS.keys():
        is_healthy = check_backend_health(backend_name)

        # Update consecutive counters
        if is_healthy:
            backend_status[backend_name]["consecutive_successes"] += 1
            backend_status[backend_name]["consecutive_failures"] = 0
        else:
            backend_status[backend_name]["consecutive_failures"] += 1
            backend_status[backend_name]["consecutive_successes"] = 0

        # Update health status based on thresholds
        if backend_status[backend_name]["consecutive_failures"] >= 3:
            backend_status[backend_name]["healthy"] = False
        elif backend_status[backend_name]["consecutive_successes"] >= 2:
            backend_status[backend_name]["healthy"] = True

        backend_status[backend_name]["last_check"] = current_time

        status_text = "healthy" if backend_status[backend_name]["healthy"] else "unhealthy"
        logger.info(f"Backend {backend_name} status: {status_text}")


@app.route('/ocr/image', methods=['POST'])
def ocr_image():
    """
    Process single image OCR request by routing to specified backend.

    Client request format:
    {
        "image": file,
        "backend": "deepseek-ocr" | "mineru",
        "prompt": "optional custom prompt"
    }
    """
    start_time = time.time()

    # Validate request
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    backend_name = request.form.get('backend')
    if not backend_name:
        return jsonify({"error": "No backend specified"}), 400

    if backend_name not in BACKEND_CONFIGS:
        return jsonify({"error": f"Invalid backend: {backend_name}"}), 400

    # Check if backend is healthy
    if not backend_status[backend_name]["healthy"]:
        return jsonify({
            "error": f"Backend {backend_name} is currently unavailable",
            "backend": backend_name,
            "suggested_action": "Try again later or use the other backend"
        }), 503

    image_file = request.files['image']
    prompt = request.form.get('prompt', '')

    # Save uploaded file temporarily
    temp_path = f"/tmp/{image_file.filename}"
    image_file.save(temp_path)

    try:
        # Route request to appropriate backend
        backend_url = get_backend_image_ocr_url(backend_name)

        # Prepare files and data for backend request
        files = {'image': (image_file.filename, open(temp_path, 'rb'), image_file.content_type)}
        data = {'prompt': prompt} if prompt else {}

        # Forward request to backend
        response = requests.post(
            backend_url,
            files=files,
            data=data,
            timeout=TIMEOUT_CONFIG["ocr_request"]
        )

        processing_time = time.time() - start_time

        if response.status_code == 200:
            # Return backend response directly (already in unified format)
            backend_response = response.json()
            backend_response["processing_time"] = processing_time
            return jsonify(backend_response)
        else:
            # Handle backend error
            logger.error(f"Backend {backend_name} returned error: {response.status_code}")
            return jsonify({
                "error": f"Backend {backend_name} processing failed",
                "backend": backend_name,
                "status_code": response.status_code,
                "processing_time": processing_time
            }), 500

    except requests.exceptions.Timeout:
        processing_time = time.time() - start_time
        logger.error(f"Backend {backend_name} request timed out")
        return jsonify({
            "error": f"Backend {backend_name} request timed out",
            "backend": backend_name,
            "processing_time": processing_time
        }), 504

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error routing to backend {backend_name}: {e}")
        return jsonify({
            "error": f"Error routing to backend {backend_name}: {str(e)}",
            "backend": backend_name,
            "processing_time": processing_time
        }), 500

    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass


@app.route('/ocr/pdf', methods=['POST'])
def ocr_pdf():
    """
    Process PDF OCR request by routing to specified backend.

    Client request format:
    {
        "pdf": file,
        "backend": "deepseek-ocr" | "mineru",
        "prompt": "optional custom prompt"
    }
    """
    start_time = time.time()

    # Validate request
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    backend_name = request.form.get('backend')
    if not backend_name:
        return jsonify({"error": "No backend specified"}), 400

    if backend_name not in BACKEND_CONFIGS:
        return jsonify({"error": f"Invalid backend: {backend_name}"}), 400

    # Check if backend is healthy
    if not backend_status[backend_name]["healthy"]:
        return jsonify({
            "error": f"Backend {backend_name} is currently unavailable",
            "backend": backend_name,
            "suggested_action": "Try again later or use the other backend"
        }), 503

    pdf_file = request.files['pdf']
    prompt = request.form.get('prompt', '')

    # Save uploaded file temporarily
    temp_path = f"/tmp/{pdf_file.filename}"
    pdf_file.save(temp_path)

    try:
        # Route request to appropriate backend
        backend_url = get_backend_pdf_ocr_url(backend_name)

        # Prepare files and data for backend request
        files = {'pdf': (pdf_file.filename, open(temp_path, 'rb'), pdf_file.content_type)}
        data = {'prompt': prompt} if prompt else {}

        # Forward request to backend
        response = requests.post(
            backend_url,
            files=files,
            data=data,
            timeout=TIMEOUT_CONFIG["ocr_request"]
        )

        processing_time = time.time() - start_time

        if response.status_code == 200:
            # Return backend response directly (already in unified format)
            backend_response = response.json()
            backend_response["processing_time"] = processing_time
            return jsonify(backend_response)
        else:
            # Handle backend error
            logger.error(f"Backend {backend_name} returned error: {response.status_code}")
            return jsonify({
                "error": f"Backend {backend_name} processing failed",
                "backend": backend_name,
                "status_code": response.status_code,
                "processing_time": processing_time
            }), 500

    except requests.exceptions.Timeout:
        processing_time = time.time() - start_time
        logger.error(f"Backend {backend_name} request timed out")
        return jsonify({
            "error": f"Backend {backend_name} request timed out",
            "backend": backend_name,
            "processing_time": processing_time
        }), 504

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error routing to backend {backend_name}: {e}")
        return jsonify({
            "error": f"Error routing to backend {backend_name}: {str(e)}",
            "backend": backend_name,
            "processing_time": processing_time
        }), 500

    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for orchestrator and backends.

    Returns comprehensive health status including:
    - Orchestrator status
    - Individual backend status
    - System-wide health summary
    """
    # Update backend health status before responding
    update_backend_health_status()

    # Build detailed health response
    backend_health = {}
    for backend_name in BACKEND_CONFIGS.keys():
        backend_health[backend_name] = {
            "healthy": backend_status[backend_name]["healthy"],
            "last_check": backend_status[backend_name]["last_check"],
            "config": BACKEND_CONFIGS[backend_name]
        }

    # Determine overall system health
    all_healthy = all(status["healthy"] for status in backend_status.values())
    any_healthy = any(status["healthy"] for status in backend_status.values())

    system_status = "healthy" if all_healthy else "degraded" if any_healthy else "unhealthy"

    return jsonify({
        "status": system_status,
        "orchestrator": {
            "healthy": True,
            "timestamp": time.time(),
            "version": "1.0.0"
        },
        "backends": backend_health,
        "system_summary": {
            "total_backends": len(BACKEND_CONFIGS),
            "healthy_backends": sum(1 for status in backend_status.values() if status["healthy"]),
            "unhealthy_backends": sum(1 for status in backend_status.values() if not status["healthy"])
        }
    })


@app.route('/backends', methods=['GET'])
def list_backends():
    """
    List available backends with their capabilities and status.

    Returns detailed information about each backend including:
    - Backend name and description
    - Current health status
    - GPU assignment
    - Supported operations
    """
    # Update backend health status before responding
    update_backend_health_status()

    backends_info = {}
    for backend_name, config in BACKEND_CONFIGS.items():
        backends_info[backend_name] = {
            "description": config["description"],
            "gpu": config["gpu"],
            "healthy": backend_status[backend_name]["healthy"],
            "endpoints": {
                "health": get_backend_health_url(backend_name),
                "image_ocr": get_backend_image_ocr_url(backend_name),
                "pdf_ocr": get_backend_pdf_ocr_url(backend_name)
            },
            "last_check": backend_status[backend_name]["last_check"]
        }

    return jsonify({
        "available_backends": list(BACKEND_CONFIGS.keys()),
        "backends": backends_info,
        "timestamp": time.time()
    })


if __name__ == '__main__':
    # Perform initial health check on startup
    logger.info("Performing initial backend health checks...")
    update_backend_health_status()

    # Start Flask server
    logger.info(f"Starting OCR Orchestrator server on {SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}...")
    app.run(
        host=SERVER_CONFIG['host'],
        port=SERVER_CONFIG['port'],
        debug=SERVER_CONFIG['debug'],
        threaded=SERVER_CONFIG['threaded']
    )