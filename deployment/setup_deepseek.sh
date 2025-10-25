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
uv pip install --upgrade pip

# Force correct NumPy version (required by DeepSeek-OCR)
echo "Installing NumPy 1.26.4 (required version)..."
uv pip install --force-reinstall numpy==1.26.4

# Install vLLM 0.8.5 (official supported version) - EXACTLY like reference
echo "Installing vLLM 0.8.5 (official supported version)..."
uv pip install vllm==0.8.5

# Install required packages from official DeepSeek-OCR requirements
echo "Installing required packages from official requirements..."
uv pip install PyMuPDF img2pdf einops easydict addict Pillow

# Install server dependencies
echo "Installing server dependencies..."
uv pip install flask flask-cors

# Install optional packages (may fail on some systems)
echo "Installing optional packages..."
uv pip install matplotlib || echo "⚠ matplotlib installation failed (optional)"

# Install flash-attn (MUST HAVE for optimal performance)
echo "🚀 Installing flash-attn (MUST HAVE for optimal performance)..."

# Detect CUDA Toolkit installation
echo "🔍 Checking CUDA Toolkit installation..."

# Check multiple possible CUDA installation locations
CUDA_PATHS="/usr/local/cuda-12.1 /usr/local/cuda /opt/cuda"
CUDA_HOME=""

for path in $CUDA_PATHS; do
    if [ -d "$path" ] && [ -f "$path/bin/nvcc" ]; then
        CUDA_HOME="$path"
        echo "✅ CUDA Toolkit found at: $CUDA_HOME"
        break
    fi

    # Also check if nvcc is in PATH
    if command -v nvcc >/dev/null 2>&1; then
        CUDA_HOME=$(dirname $(dirname $(which nvcc)))
        echo "✅ CUDA Toolkit found via PATH at: $CUDA_HOME"
        break
    fi
done

if [ -n "$CUDA_HOME" ]; then
    export CUDA_HOME
    export PATH=$CUDA_HOME/bin:$PATH
    export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
else
    echo "❌ CUDA Toolkit not found. Installing CUDA 12.1 (compatible with flash-attn)..."

    # Check if CUDA installer already exists to avoid re-downloading
    if [ ! -f "cuda_12.1.0_530.30.02_linux.run" ]; then
        wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
    fi

    chmod +x cuda_12.1.0_530.30.02_linux.run
    sudo ./cuda_12.1.0_530.30.02_linux.run --silent --toolkit --override

    export CUDA_HOME=/usr/local/cuda-12.1
    export PATH=$CUDA_HOME/bin:$PATH
    export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

    echo "✅ CUDA Toolkit 12.1 installed at: $CUDA_HOME"
fi

# Install wheel first (required for flash-attn build but not declared as dependency)
uv pip install wheel
echo "Installing flash-attn with CUDA support..."

# Install flash-attn with CUDA Toolkit - NO FALLBACKS, NO PRE-BUILT WHEELS
uv pip install flash-attn --no-build-isolation

# Download DeepSeek OCR model using simple approach (avoids UI freezing)
echo "📥 Downloading DeepSeek OCR model..."
MODEL_DIR="../models/deepseek-ocr"
mkdir -p "$MODEL_DIR"

# Check if model already exists (avoid re-downloading)
echo "🔍 Checking if model already exists..."
REQUIRED_FILES=("model.safetensors" "config.json" "tokenizer.json" "tokenizer_config.json" "vocab.json")
MODEL_EXISTS=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$MODEL_DIR/$file" ]; then
        echo "❌ Missing required file: $file"
        MODEL_EXISTS=false
        break
    fi
    echo "✅ Found: $file"
done

if [ "$MODEL_EXISTS" = true ]; then
    echo "✅ Model already exists with all required files, skipping download"
else
    # Download using huggingface_hub with token from environment variable
    echo "🚀 Downloading DeepSeek OCR model with authentication..."
    echo "Using HUGGINGFACE_HUB_TOKEN: ${HUGGINGFACE_HUB_TOKEN:0:10}..."
    HUGGINGFACE_HUB_TOKEN="$HUGGINGFACE_HUB_TOKEN" python3 -c "
from huggingface_hub import snapshot_download
import os

MODEL_DIR = '$MODEL_DIR'
REPO_ID = 'deepseek-ai/DeepSeek-OCR'

print('Downloading DeepSeek OCR model...')
try:
    snapshot_download(
        repo_id=REPO_ID,
        local_dir=MODEL_DIR,
        force_download=False,
        local_dir_use_symlinks=False,
        token=os.environ.get('HUGGINGFACE_HUB_TOKEN')
    )
    print('✅ DeepSeek OCR model downloaded successfully!')
except Exception as e:
    print(f'❌ DeepSeek OCR model download failed: {e}')
    print('Please set HUGGINGFACE_HUB_TOKEN environment variable with your Hugging Face token')
    print('export HUGGINGFACE_HUB_TOKEN=your_token_here')
    exit(1)
"
fi

# Verify installations
echo "Verifying installations..."
python -c "import numpy; print(f'✓ NumPy: {numpy.__version__}')"
python -c "import torch; print(f'✓ PyTorch: {torch.__version__}')"
python -c "import torch; print(f'✓ CUDA available: {torch.cuda.is_available()}')"
python -c "import vllm; print(f'✓ vLLM: {vllm.__version__}')"
python -c "import transformers; print(f'✓ Transformers: {transformers.__version__}')"
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