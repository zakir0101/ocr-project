#!/bin/bash

# Server Health and Model Loading Test Script
# This script tests server states and validates that models are loaded into GPU memory
# Note: This script should be used after running ./deploy.sh

set -e  # Exit on any error

echo "=========================================="
echo "Server Health and Model Loading Test"
echo "=========================================="

# Function to test health endpoint
test_health_endpoint() {
    local name=$1
    local port=$2
    local url="http://localhost:$port/health"

    echo ""
    echo "🧪 Testing $name health endpoint..."
    echo "   URL: $url"

    if curl -s --max-time 10 "$url" > /dev/null; then
        echo "   ✅ $name is responding"

        # Get detailed health status
        response=$(curl -s "$url")
        echo "   📊 Health status:"
        echo "      $response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for key, value in data.items():
    print(f'        {key}: {value}')
"
        return 0
    else
        echo "   ❌ $name is not responding"
        return 1
    fi
}

# Function to test model loading
test_model_loading() {
    local name=$1
    local port=$2

    echo ""
    echo "🧪 Testing $name model loading..."

    health_response=$(curl -s "http://localhost:$port/health")
    model_loaded=$(echo "$health_response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('model_loaded', False))
")

    if [ "$model_loaded" = "True" ]; then
        echo "   ✅ $name model is loaded"

        # Get model loading details
        backend=$(echo "$health_response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('backend', 'unknown'))")
        gpu_available=$(echo "$health_response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('gpu_available', False))")

        echo "   📊 Model details:"
        echo "      - Backend: $backend"
        echo "      - GPU available: $gpu_available"

        return 0
    else
        echo "   ❌ $name model is NOT loaded"
        echo "   📋 Debug info:"
        echo "      $health_response"
        return 1
    fi
}

# Function to test GPU memory usage
test_gpu_memory() {
    local name=$1
    local port=$2

    echo ""
    echo "🧪 Testing $name GPU memory..."

    # This would require additional endpoints or system monitoring
    # For now, we'll check if GPU is available and model is loaded
    health_response=$(curl -s "http://localhost:$port/health")
    gpu_available=$(echo "$health_response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('gpu_available', False))
")

    if [ "$gpu_available" = "True" ]; then
        echo "   ✅ $name GPU is available"

        # Check if we can get GPU memory info (this would need server enhancement)
        echo "   ℹ️  GPU memory monitoring would require server enhancement"
        return 0
    else
        echo "   ❌ $name GPU is NOT available"
        return 1
    fi
}

# Main test sequence

# Test orchestrator
test_health_endpoint "Orchestrator" 8080

# Test DeepSeek backend
test_health_endpoint "DeepSeek Backend" 5000
test_model_loading "DeepSeek" 5000
test_gpu_memory "DeepSeek" 5000

# Test Mineru backend
test_health_endpoint "Mineru Backend" 5001
test_model_loading "Mineru" 5001
test_gpu_memory "Mineru" 5001

echo ""
echo "=========================================="
echo "✅ Server Health and Model Loading Summary"
echo "=========================================="
echo ""
echo "📊 Results:"
echo "   - Orchestrator: Port 8080"
echo "   - DeepSeek Backend: Port 5000 (GPU 0)"
echo "   - Mineru Backend: Port 5001 (GPU 1)"
echo ""
echo "🎯 Success Criteria:"
echo "   ✓ All servers are responding"
echo "   ✓ Models are loaded into GPU memory"
echo "   ✓ GPU resources are available"
echo ""
echo "⚠️  Note: GPU memory monitoring requires server enhancement"
echo "=========================================="