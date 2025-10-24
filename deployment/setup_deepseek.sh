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

# Install uv for better dependency management
echo "Installing uv for package management..."
pip install uv

# Install vLLM with automatic PyTorch backend selection (recommended approach)
echo "Installing vLLM with automatic PyTorch backend selection..."
uv pip install vllm==0.8.5 --torch-backend=auto

# Force correct NumPy version (required by DeepSeek-OCR)
echo "Installing NumPy 1.26.4 (required version)..."
uv pip install numpy==1.26.4

# Install required packages from official DeepSeek-OCR requirements
echo "Installing required packages from official requirements..."
uv pip install transformers==4.46.3 tokenizers==0.20.3
uv pip install PyMuPDF img2pdf einops easydict addict Pillow

# Install server dependencies
echo "Installing server dependencies..."
uv pip install flask flask-cors

# Install optional packages (may fail on some systems)
echo "Installing optional packages..."
uv pip install matplotlib || echo "⚠ matplotlib installation failed (optional)"

# Install flash-attn (required for optimal performance)
echo "Installing flash-attn (required for optimal performance)..."
# Set CUDA_HOME environment variable if not already set
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda}
echo "✓ Set CUDA_HOME=$CUDA_HOME for flash-attn build"

# Install wheel first (required for flash-attn build but not declared as dependency)
uv pip install wheel
echo "Installing flash-attn with CUDA support..."
uv pip install flash-attn --no-build-isolation

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