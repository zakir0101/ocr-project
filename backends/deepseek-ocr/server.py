"""
DeepSeek OCR Backend Server

Flask server implementation for DeepSeek OCR backend using the OCRBackend interface.
This server runs on port 5000 and uses GPU 0 exclusively.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from deepseek_ocr_backend import DeepSeekOCRBackend

# Initialize Flask app
app = Flask(__name__)

# Global backend instance
backend = None

@app.route('/ocr/image', methods=['POST'])
def ocr_image():
    """Process single image OCR request"""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']

    # Save uploaded file temporarily
    temp_path = f"/tmp/{image_file.filename}"
    image_file.save(temp_path)

    try:
        # Process image with backend
        result = backend.ocr_image(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {str(e)}"}), 500
    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass

@app.route('/ocr/pdf', methods=['POST'])
def ocr_pdf():
    """Process PDF OCR request"""
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files['pdf']

    # Save uploaded file temporarily
    temp_path = f"/tmp/{pdf_file.filename}"
    pdf_file.save(temp_path)

    try:
        # Process PDF with backend
        result = backend.ocr_pdf(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"PDF processing failed: {str(e)}"}), 500
    finally:
        # Clean up temporary file
        try:
            os.remove(temp_path)
        except:
            pass

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if backend:
        status = backend.get_health_status()
        return jsonify(status)
    else:
        return jsonify({
            "status": "unhealthy",
            "model_loaded": False,
            "gpu_available": False,
            "backend": "deepseek-ocr",
            "timestamp": time.time()
        })

if __name__ == '__main__':
    # Initialize backend on startup
    # Model path from deployment setup
    model_path = "../../models/deepseek-ocr"
    backend = DeepSeekOCRBackend(model_path=model_path)

    if backend.load_model():
        print("✓ DeepSeek backend initialized successfully")
    else:
        print("✗ Failed to initialize DeepSeek backend")

    # Start Flask server on port 5000
    print("Starting DeepSeek OCR backend server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)