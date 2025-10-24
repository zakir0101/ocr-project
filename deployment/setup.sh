#!/bin/bash

# Multi-backend OCR System - Main Setup Script
# This script orchestrates the setup of all components

set -e  # Exit on any error

echo "🚀 Starting Multi-backend OCR System Setup..."
echo "=============================================="

# Create main virtual environment
echo "📦 Creating main virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install shared dependencies
echo "📦 Installing shared dependencies..."
pip install --upgrade pip
pip install -r ../requirements.txt

# Run DeepSeek backend setup
echo "🔧 Setting up DeepSeek backend..."
if ./setup_deepseek.sh; then
    echo "✅ DeepSeek backend setup completed"
else
    echo "❌ DeepSeek backend setup failed"
    exit 1
fi

# Run Mineru backend setup
echo "🔧 Setting up Mineru backend..."
if ./setup_mineru.sh; then
    echo "✅ Mineru backend setup completed"
else
    echo "❌ Mineru backend setup failed"
    exit 1
fi

# Run orchestrator setup
echo "🔧 Setting up orchestrator..."
if ./setup_orchestrator.sh; then
    echo "✅ Orchestrator setup completed"
else
    echo "❌ Orchestrator setup failed"
    exit 1
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Start the system: ./startup.sh"
echo "   2. Check health: curl http://localhost:8080/health"
echo "   3. Test individual backends:"
echo "      - DeepSeek: curl http://localhost:5000/health"
echo "      - Mineru: curl http://localhost:5001/health"
echo ""
echo "🔧 System components:"
echo "   - Orchestrator: http://localhost:8080"
echo "   - DeepSeek backend: http://localhost:5000 (GPU 0)"
echo "   - Mineru backend: http://localhost:5001 (GPU 1)"