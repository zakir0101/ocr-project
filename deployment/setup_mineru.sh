#!/bin/bash

# Mineru Backend Setup Script
# This script sets up the Mineru backend with virtual environment and dependencies

set -e  # Exit on any error

echo "=========================================="
echo "Mineru Backend Setup"
echo "=========================================="

# Set GPU isolation for Mineru
export CUDA_VISIBLE_DEVICES="1"
echo "✓ Set CUDA_VISIBLE_DEVICES=1 for GPU isolation"

# Create Mineru virtual environment
echo "📦 Creating Mineru virtual environment..."
python3 -m venv ../backends/mineru/venv
source ../backends/mineru/venv/bin/activate

# Install dependencies
echo "📦 Installing Mineru dependencies..."
pip install --upgrade pip

# Install uv for faster package management
echo "Installing uv for package management..."
pip install uv

# Install MinerU core package with increased timeout for large CUDA packages
echo "Installing MinerU core package..."
export UV_HTTP_TIMEOUT=300
uv pip install -U "mineru[core]"

# Install server dependencies
echo "Installing server dependencies..."
uv pip install flask flask-cors Pillow

# Install optional packages
echo "Installing optional packages..."
uv pip install opencv-python || echo "⚠ OpenCV installation failed (optional)"

# Verify installations
echo "Verifying installations..."
# python -c "import mineru; print(f'✓ MinerU: {mineru.__version__}')"
python -c "import flask; print(f'✓ Flask: {flask.__version__}')"
python -c "import torch; print(f'✓ PyTorch: {torch.__version__}')"

# Download Mineru model (if needed)
echo "📥 Setting up Mineru model..."
MODEL_DIR="../models/mineru"
mkdir -p "$MODEL_DIR"

# Mineru models are typically downloaded automatically on first use
echo "⚠️  Mineru models will be downloaded automatically on first use"
echo "   Model directory: $MODEL_DIR"

echo ""
echo "=========================================="
echo "✅ Mineru backend setup completed!"
echo "=========================================="
echo "   Virtual environment: ../backends/mineru/venv"
echo "   Model directory: $MODEL_DIR"
echo "   Server port: 5001"
echo "   GPU: 1 (CUDA_VISIBLE_DEVICES=1)"
echo ""
echo "Next steps:"
echo "   1. Activate environment: source ../backends/mineru/venv/bin/activate"
echo "   2. Start server: python ../backends/mineru/server.py"
echo "   3. Test: curl http://localhost:5001/health"
echo ""
echo "Hardware requirements:"
echo "   - GPU: Turing architecture and later, 8GB+ VRAM"
echo "   - Memory: Minimum 16GB+, recommended 32GB+"
echo "   - Disk: 20GB+, SSD recommended"
echo "=========================================="
