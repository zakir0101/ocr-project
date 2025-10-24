#!/bin/bash

# Orchestrator Setup Script
# This script sets up the orchestrator with virtual environment and dependencies

set -e  # Exit on any error

echo "=========================================="
echo "Orchestrator Setup"
echo "=========================================="

# Create orchestrator virtual environment
echo "📦 Creating orchestrator virtual environment..."
python3 -m venv ../orchestrator/venv
source ../orchestrator/venv/bin/activate

# Install dependencies
echo "📦 Installing orchestrator dependencies..."
pip install --upgrade pip

# Install core dependencies
echo "Installing core dependencies..."
pip install flask flask-cors requests Pillow

# Install additional utilities
echo "Installing additional utilities..."
pip install numpy opencv-python

# Verify installations
echo "Verifying installations..."
python -c "import flask; print(f'✓ Flask: {flask.__version__}')"
python -c "import requests; print(f'✓ Requests: {requests.__version__}')"

# Create necessary directories
echo "📁 Creating orchestrator directories..."
mkdir -p ../orchestrator/logs
mkdir -p ../orchestrator/temp

echo ""
echo "=========================================="
echo "✅ Orchestrator setup completed!"
echo "=========================================="
echo "   Virtual environment: ../orchestrator/venv"
echo "   Server port: 8080"
echo "   Log directory: ../orchestrator/logs"
echo "   Temp directory: ../orchestrator/temp"
echo ""
echo "Next steps:"
echo "   1. Activate environment: source ../orchestrator/venv/bin/activate"
echo "   2. Start server: python ../orchestrator/server.py"
echo "   3. Test: curl http://localhost:8080/health"
echo ""
echo "Orchestrator endpoints:"
echo "   - POST /ocr/image - Process image OCR with specified backend"
echo "   - GET /health - System health status"
echo "   - GET /backends - Available backend status"
echo "=========================================="