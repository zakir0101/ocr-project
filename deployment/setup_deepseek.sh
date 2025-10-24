#!/bin/bash

# DeepSeek Backend Setup Script
# This script sets up the DeepSeek OCR backend with virtual environment and dependencies

set -e  # Exit on any error

echo "=========================================="
echo "DeepSeek OCR Backend Setup"
echo "=========================================="

# Set environment variables for compatibility
export VLLM_USE_V1=0
echo "✓ Set VLLM_USE_V1=0 for legacy API compatibility"

# Create DeepSeek virtual environment
echo "📦 Creating DeepSeek virtual environment..."
python3 -m venv ../backends/deepseek-ocr/venv
source ../backends/deepseek-ocr/venv/bin/activate

# Install dependencies
echo "📦 Installing DeepSeek dependencies..."
pip install --upgrade pip

# Install vLLM with PyTorch compatibility (use pip for pre-built wheels)
echo "Installing vLLM with PyTorch compatibility..."
pip install --timeout 600 vllm==0.8.5

# Force correct NumPy version (required by DeepSeek-OCR)
echo "Installing NumPy 1.26.4 (required version)..."
pip install --force-reinstall numpy==1.26.4

# Install required packages from official DeepSeek-OCR requirements
echo "Installing required packages from official requirements..."
pip install transformers==4.46.3 tokenizers==0.20.3
pip install PyMuPDF img2pdf einops easydict addict Pillow

# Install server dependencies
echo "Installing server dependencies..."
pip install flask flask-cors

# Install optional packages (may fail on some systems)
echo "Installing optional packages..."
pip install matplotlib || echo "⚠ matplotlib installation failed (optional)"

# Try flash-attn (optional, may fail without CUDA_HOME)
echo "Attempting to install flash-attn (optional)..."
pip install flash-attn --no-build-isolation || echo "⚠ Flash attention optional, continuing without it..."

# Download DeepSeek OCR model
echo "📥 Downloading DeepSeek OCR model..."
MODEL_DIR="../models/deepseek-ocr"
mkdir -p "$MODEL_DIR"

# Download using huggingface_hub
echo "Downloading model from HuggingFace..."
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='deepseek-ai/DeepSeek-OCR',
    local_dir='$MODEL_DIR',
    local_dir_use_symlinks=False
)
"

# Verify installations
echo "Verifying installations..."
python -c "import numpy; print(f'✓ NumPy: {numpy.__version__}')"
python -c "import vllm; print(f'✓ vLLM: {vllm.__version__}')"
python -c "import transformers; print(f'✓ Transformers: {transformers.__version__}')"
python -c "import torch; print(f'✓ PyTorch: {torch.__version__}')"
python -c "import flask; print(f'✓ Flask: {flask.__version__}')"

echo ""
echo "=========================================="
echo "✅ DeepSeek backend setup completed!"
echo "=========================================="
echo "   Virtual environment: ../backends/deepseek-ocr/venv"
echo "   Model directory: $MODEL_DIR"
echo "   Server port: 5000"
echo "   GPU: 0 (CUDA_VISIBLE_DEVICES=0)"
echo ""
echo "Next steps:"
echo "   1. Activate environment: source ../backends/deepseek-ocr/venv/bin/activate"
echo "   2. Start server: python ../backends/deepseek-ocr/server.py"
echo "   3. Test: curl http://localhost:5000/health"
echo ""
echo "Compatible GPU architectures: sm_50, sm_60, sm_70, sm_75, sm_80, sm_86, sm_89, sm_90"
echo "Incompatible: sm_120 (RTX 5080)"
echo "=========================================="