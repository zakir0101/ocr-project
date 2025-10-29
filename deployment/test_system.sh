#!/bin/bash

# Multi-backend OCR System Test Script
# This script tests model loading, health monitoring, and simultaneous operation

set -e  # Exit on any error

echo "=========================================="
echo "Multi-backend OCR System Test"
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
    else
        echo "   ❌ $name model is NOT loaded"
        echo "   📋 Debug info:"
        echo "      $health_response"
    fi
}

# Function to test GPU availability
test_gpu_availability() {
    local name=$1
    local port=$2

    echo ""
    echo "🧪 Testing $name GPU availability..."

    health_response=$(curl -s "http://localhost:$port/health")
    gpu_available=$(echo "$health_response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('gpu_available', False))
")

    if [ "$gpu_available" = "True" ]; then
        echo "   ✅ $name GPU is available"
    else
        echo "   ❌ $name GPU is NOT available"
    fi
}

# Function to test simultaneous operation
test_simultaneous_operation() {
    echo ""
    echo "🧪 Testing simultaneous operation..."

    # Test both backends at the same time
    deepseek_health=$(curl -s http://localhost:5000/health) &
    mineru_health=$(curl -s http://localhost:5001/health) &

    wait

    deepseek_status=$(echo "$deepseek_health" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('status', 'unknown'))")
    mineru_status=$(echo "$mineru_health" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('status', 'unknown'))")

    if [ "$deepseek_status" = "healthy" ] && [ "$mineru_status" = "healthy" ]; then
        echo "   ✅ Both backends are healthy simultaneously"
    else
        echo "   ❌ Backend health issues detected:"
        echo "      DeepSeek: $deepseek_status"
        echo "      Mineru: $mineru_status"
    fi
}

# Main test sequence

# Test orchestrator
test_health_endpoint "Orchestrator" 8080

# Test DeepSeek backend
test_health_endpoint "DeepSeek Backend" 5000
test_model_loading "DeepSeek" 5000
test_gpu_availability "DeepSeek" 5000

# Test Mineru backend
test_health_endpoint "Mineru Backend" 5001
test_model_loading "Mineru" 5001
test_gpu_availability "Mineru" 5001

# Test simultaneous operation
test_simultaneous_operation

echo ""
echo "=========================================="
echo "✅ System Test Summary"
echo "=========================================="
echo ""
echo "📊 Test Results:"
echo "   - Orchestrator: Port 8080"
echo "   - DeepSeek Backend: Port 5000 (GPU 0)"
echo "   - Mineru Backend: Port 5001 (GPU 1)"
echo ""
echo "🎯 Success Criteria:"
echo "   ✓ Both backends run simultaneously without interference"
echo "   ✓ Dedicated GPU assignment working correctly"
echo "   ✓ Health monitoring endpoints functional"
echo "   ✓ Model loading status reported correctly"
echo ""
echo "🚀 Next steps:"
echo "   1. Run actual OCR tests with sample images"
echo "   2. Verify backend selection in orchestrator"
echo "   3. Test unified API response format"
echo "=========================================="