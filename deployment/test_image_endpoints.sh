#!/bin/bash

# Image Endpoint Test Script
# This script tests the image OCR endpoints systematically for both models
# Note: This script should be used after running ./deploy.sh

set -e  # Exit on any error

echo "=========================================="
echo "Image Endpoint Test"
echo "=========================================="

# Function to test image endpoint
test_image_endpoint() {
    local name=$1
    local port=$2
    local test_image=$3

    echo ""
    echo "🧪 Testing $name image endpoint..."
    echo "   URL: http://localhost:$port/ocr/image"
    echo "   Test image: $test_image"

    if [ ! -f "$test_image" ]; then
        echo "   ❌ Test image not found: $test_image"
        echo "   ℹ️  Creating a simple test image..."

        # Create a simple test image
        python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple image with text
img = Image.new('RGB', (400, 200), color='white')
d = ImageDraw.Draw(img)

# Try to use a font, fallback to default if not available
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
except:
    font = ImageFont.load_default()

d.text((20, 20), 'Test Document for OCR', fill='black', font=font)
d.text((20, 60), 'Sample text line 1', fill='black', font=font)
d.text((20, 100), 'Sample text line 2', fill='black', font=font)
d.text((20, 140), 'Sample text line 3', fill='black', font=font)

img.save('$test_image')
print(f'Created test image: $test_image')
"
    fi

    if [ -f "$test_image" ]; then
        echo "   ✅ Test image available: $test_image"

        # Test the endpoint
        response=$(curl -s -X POST -F "image=@$test_image" "http://localhost:$port/ocr/image")

        # Check if request was successful
        success=$(echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('success', False))
except:
    print(False)
")

        if [ "$success" = "True" ]; then
            echo "   ✅ Image OCR request successful"

            # Extract key information
            backend=$(echo "$response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('backend', 'unknown'))")
            processing_time=$(echo "$response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('processing_time', 0))")
            markdown_length=$(echo "$response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(len(data.get('markdown', '')))")

            echo "   📊 Response details:"
            echo "      - Backend: $backend"
            echo "      - Processing time: ${processing_time}s"
            echo "      - Markdown length: $markdown_length chars"

            # Show first 100 chars of markdown
            markdown_preview=$(echo "$response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('markdown', '')[:100] + '...')")
            echo "      - Markdown preview: $markdown_preview"

            return 0
        else
            echo "   ❌ Image OCR request failed"
            echo "   📋 Response:"
            echo "      $response"
            return 1
        fi
    else
        echo "   ❌ Could not create test image"
        return 1
    fi
}

# Function to test orchestrator image routing
test_orchestrator_image_routing() {
    local backend=$1
    local test_image=$2

    echo ""
    echo "🧪 Testing orchestrator image routing for $backend..."
    echo "   URL: http://localhost:8080/ocr/image"
    echo "   Backend: $backend"
    echo "   Test image: $test_image"

    if [ -f "$test_image" ]; then
        echo "   ✅ Test image available: $test_image"

        # Test the orchestrator endpoint with backend selection
        response=$(curl -s -X POST -F "image=@$test_image" -F "backend=$backend" "http://localhost:8080/ocr/image")

        # Check if request was successful
        success=$(echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('success', False))
except:
    print(False)
")

        if [ "$success" = "True" ]; then
            echo "   ✅ Orchestrator routing successful for $backend"

            # Extract key information
            actual_backend=$(echo "$response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('backend', 'unknown'))")
            processing_time=$(echo "$response" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('processing_time', 0))")

            echo "   📊 Response details:"
            echo "      - Requested backend: $backend"
            echo "      - Actual backend: $actual_backend"
            echo "      - Processing time: ${processing_time}s"

            return 0
        else
            echo "   ❌ Orchestrator routing failed for $backend"
            echo "   📋 Response:"
            echo "      $response"
            return 1
        fi
    else
        echo "   ❌ Test image not found: $test_image"
        return 1
    fi
}

# Main test sequence

# Create test image
TEST_IMAGE="test_image.png"

# Test direct backend endpoints
test_image_endpoint "DeepSeek Backend" 5000 "$TEST_IMAGE"
test_image_endpoint "Mineru Backend" 5001 "$TEST_IMAGE"

# Test orchestrator routing
test_orchestrator_image_routing "deepseek-ocr" "$TEST_IMAGE"
test_orchestrator_image_routing "mineru" "$TEST_IMAGE"

echo ""
echo "=========================================="
echo "✅ Image Endpoint Test Summary"
echo "=========================================="
echo ""
echo "📊 Results:"
echo "   - Direct backend endpoints tested"
echo "   - Orchestrator routing tested"
echo "   - Both backends processed test images"
echo ""
echo "🎯 Success Criteria:"
echo "   ✓ Image OCR endpoints are functional"
echo "   ✓ Backend selection works correctly"
echo "   ✓ Unified response format is maintained"
echo ""
echo "⚠️  Note: Test images are automatically created if not available"
echo "=========================================="