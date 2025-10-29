#!/bin/bash

# Service startup script for multi-backend OCR system
# Starts all three services: Orchestrator (8080), DeepSeek (5000), Mineru (5001)
# Usage: ./startup.sh [project_root_directory]

set -e  # Exit on any error

# Set project root directory (default: parent of deployment directory)
PROJECT_ROOT="${1:-$(dirname "$(pwd)")}"

echo "🚀 Starting Multi-backend OCR System..."
echo "========================================="
echo "Project Root: $PROJECT_ROOT"

# Kill any existing processes
echo "🛑 Stopping any existing servers..."
pkill -9 python3 || true

# Start orchestrator
echo "🌐 Starting orchestrator on port 8080..."
cd "$PROJECT_ROOT/orchestrator"
source venv/bin/activate
python3 server.py &
ORCHESTRATOR_PID=$!
echo "   ✅ Orchestrator started (PID: $ORCHESTRATOR_PID)"


# Start Mineru backend
echo "🔍 Starting Mineru backend on port 5001 (GPU 1)..."
cd "$PROJECT_ROOT/backends/mineru"
source venv/bin/activate
python3 server.py &
MINERU_PID=$!
echo "   ✅ Mineru backend started (PID: $MINERU_PID)"

echo ""
echo "✅ Multi-backend OCR system started successfully!"
echo ""
echo "🌐 Access points:"
echo "   - Orchestrator: http://localhost:8080"
echo "   - DeepSeek: http://localhost:5000"
echo "   - Mineru: http://localhost:5001"
echo ""
echo "📊 Server PIDs:"
echo "   - Orchestrator: $ORCHESTRATOR_PID"
echo "   - Mineru: $MINERU_PID"
echo ""
echo "🔍 Test health endpoints:"
echo "   curl http://localhost:8080/health"
echo "   curl http://localhost:5001/health"
