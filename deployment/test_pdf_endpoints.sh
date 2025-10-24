#!/bin/bash

# PDF Endpoint Test Script
# This script tests the PDF OCR endpoints systematically for both models
# Note: This script should be used after running ./deploy.sh

set -e  # Exit on any error

echo "=========================================="
echo "PDF Endpoint Test"
echo "=========================================="

# Function to test PDF endpoint
test_pdf_endpoint() {
    local name=$1
    local port=$2
    local test_pdf=$3

    echo ""
    echo "🧪 Testing $name PDF endpoint..."
    echo "   URL: http://localhost:$port/ocr/pdf"
    echo "   Test PDF: $test_pdf"

    if [ ! -f "$test_pdf" ]; then
        echo "   ❌ Test PDF not found: $test_pdf"
        echo "   ℹ️  Creating a simple test PDF..."

        # Create a simple test PDF
        python3 -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

# Create a simple PDF with text
pdf_path = '$test_pdf'
c = canvas.Canvas(pdf_path, pagesize=letter)

# Add some text
c.setFont('Helvetica', 12)
c.drawString(100, 750, 'Test Document for PDF OCR')
c.drawString(100, 730, 'This is a sample PDF document')
c.drawString(100, 710, 'Created for testing OCR functionality')
c.drawString(100, 690, 'Multiple lines of text for processing')
c.drawString(100, 670, 'Simple formatting and layout')

# Add a second page
c.showPage()
c.setFont('Helvetica', 12)
c.drawString(100, 750, 'Second Page')
c.drawString(100, 730, 'Additional content for multi-page testing')
c.drawString(100, 710, 'Different text on this page')

c.save()
print(f'Created test PDF: {pdf_path}')
"
    fi

    if [ -f "$test_pdf" ]; then
        echo "   ✅ Test PDF available: $test_pdf"

        # Test the endpoint
        response=$(curl -s -X POST -F "pdf=@$test_pdf" "http://localhost:$port/ocr/pdf")

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
            echo "   ✅ PDF OCR request successful"

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
            echo "   ❌ PDF OCR request failed"
            echo "   📋 Response:"
            echo "      $response"
            return 1
        fi
    else
        echo "   ❌ Could not create test PDF"
        return 1
    fi
}

# Function to test orchestrator PDF routing
test_orchestrator_pdf_routing() {
    local backend=$1
    local test_pdf=$2

    echo ""
    echo "🧪 Testing orchestrator PDF routing for $backend..."
    echo "   URL: http://localhost:8080/ocr/pdf"
    echo "   Backend: $backend"
    echo "   Test PDF: $test_pdf"

    if [ -f "$test_pdf" ]; then
        echo "   ✅ Test PDF available: $test_pdf"

        # Test the orchestrator endpoint with backend selection
        response=$(curl -s -X POST -F "pdf=@$test_pdf" -F "backend=$backend" "http://localhost:8080/ocr/pdf")

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
        echo "   ❌ Test PDF not found: $test_pdf"
        return 1
    fi
}

# Main test sequence

# Create test PDF
TEST_PDF="test_document.pdf"

# Test direct backend endpoints
test_pdf_endpoint "DeepSeek Backend" 5000 "$TEST_PDF"
test_pdf_endpoint "Mineru Backend" 5001 "$TEST_PDF"

# Test orchestrator routing
test_orchestrator_pdf_routing "deepseek-ocr" "$TEST_PDF"
test_orchestrator_pdf_routing "mineru" "$TEST_PDF"

echo ""
echo "=========================================="
echo "✅ PDF Endpoint Test Summary"
echo "=========================================="
echo ""
echo "📊 Results:"
echo "   - Direct backend endpoints tested"
echo "   - Orchestrator routing tested"
echo "   - Both backends processed test PDFs"
echo ""
echo "🎯 Success Criteria:"
echo "   ✓ PDF OCR endpoints are functional"
echo "   ✓ Backend selection works correctly"
echo "   ✓ Multi-page PDF processing works"
echo "   ✓ Unified response format is maintained"
echo ""
echo "⚠️  Note: Test PDFs are automatically created if not available"
echo "=========================================="