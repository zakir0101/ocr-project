#!/bin/bash

# Phase 3 Web Client Test Script
# Tests the enhanced web client with backend selection and comparison features

echo "🧪 Phase 3 Web Client Test Suite"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
ORCHESTRATOR_URL="http://localhost:8080"
TEST_IMAGE="test.png"

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗${NC} $message"
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}ℹ${NC} $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    fi
}

# Function to check if service is running
check_service() {
    local service_name=$1
    local url=$2

    echo -e "\n${BLUE}Testing $service_name...${NC}"

    if curl -s "$url/health" > /dev/null; then
        print_status "PASS" "$service_name is running"
        return 0
    else
        print_status "FAIL" "$service_name is not accessible"
        return 1
    fi
}

# Function to test endpoint
test_endpoint() {
    local endpoint_name=$1
    local url=$2
    local method=$3
    local data=$4

    echo -e "\n${BLUE}Testing $endpoint_name...${NC}"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$url")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST $data "$url")
    fi

    http_code=${response: -3}
    response_body=${response%???}

    if [ "$http_code" = "200" ]; then
        print_status "PASS" "$endpoint_name returned HTTP 200"
        echo "Response: $response_body" | head -c 200
        echo "..."
        return 0
    else
        print_status "FAIL" "$endpoint_name returned HTTP $http_code"
        echo "Response: $response_body"
        return 1
    fi
}

# Main test execution
echo -e "\n${BLUE}Phase 3 Web Client Validation Tests${NC}"
echo "=========================================="

# Test 1: Check orchestrator health
print_status "INFO" "Test 1: Orchestrator Health Check"
check_service "Orchestrator" "$ORCHESTRATOR_URL"

# Test 2: Check backend health status
print_status "INFO" "Test 2: Backend Health Status"
test_endpoint "Backend Health" "$ORCHESTRATOR_URL/health" "GET" ""

# Test 3: Check backend listing
print_status "INFO" "Test 3: Backend Listing"
test_endpoint "Backend List" "$ORCHESTRATOR_URL/backends" "GET" ""

# Test 4: Test single backend OCR (DeepSeek)
print_status "INFO" "Test 4: Single Backend OCR (DeepSeek)"
if [ -f "$TEST_IMAGE" ]; then
    test_endpoint "DeepSeek OCR" "$ORCHESTRATOR_URL/ocr/image" "POST" "-F image=@$TEST_IMAGE -F backend=deepseek-ocr"
else
    print_status "WARN" "Test image not found, skipping OCR test"
fi

# Test 5: Test single backend OCR (Mineru)
print_status "INFO" "Test 5: Single Backend OCR (Mineru)"
if [ -f "$TEST_IMAGE" ]; then
    test_endpoint "Mineru OCR" "$ORCHESTRATOR_URL/ocr/image" "POST" "-F image=@$TEST_IMAGE -F backend=mineru"
else
    print_status "WARN" "Test image not found, skipping OCR test"
fi

# Test 6: Test backend selection validation
print_status "INFO" "Test 6: Backend Selection Validation"
response=$(curl -s -w "%{http_code}" -X POST "$ORCHESTRATOR_URL/ocr/image" -F "image=@$TEST_IMAGE" -F "backend=invalid-backend")
http_code=${response: -3}
if [ "$http_code" = "400" ]; then
    print_status "PASS" "Invalid backend correctly rejected"
else
    print_status "FAIL" "Invalid backend should return 400 but got $http_code"
fi

# Test 7: Test response format standardization
print_status "INFO" "Test 7: Response Format Validation"
if [ -f "$TEST_IMAGE" ]; then
    response=$(curl -s "$ORCHESTRATOR_URL/ocr/image" -X POST -F "image=@$TEST_IMAGE" -F "backend=deepseek-ocr")

    # Check for required fields in response
    required_fields=("success" "backend" "raw_result" "markdown" "processing_time")
    for field in "${required_fields[@]}"; do
        if echo "$response" | grep -q "\"$field\":"; then
            print_status "PASS" "Response contains required field: $field"
        else
            print_status "FAIL" "Response missing required field: $field"
        fi
    done
else
    print_status "WARN" "Test image not found, skipping response format test"
fi

# Test 8: Test comparison mode response
print_status "INFO" "Test 8: Comparison Mode Response Structure"
if [ -f "$TEST_IMAGE" ]; then
    # Test that both backends can be called individually for comparison
    deepseek_response=$(curl -s "$ORCHESTRATOR_URL/ocr/image" -X POST -F "image=@$TEST_IMAGE" -F "backend=deepseek-ocr")
    mineru_response=$(curl -s "$ORCHESTRATOR_URL/ocr/image" -X POST -F "image=@$TEST_IMAGE" -F "backend=mineru")

    if [ -n "$deepseek_response" ] && [ -n "$mineru_response" ]; then
        print_status "PASS" "Both backends respond to individual requests"
    else
        print_status "FAIL" "One or both backends failed to respond"
    fi
else
    print_status "WARN" "Test image not found, skipping comparison test"
fi

# Test 9: Test error handling
print_status "INFO" "Test 9: Error Handling"
# Test with invalid image file
echo "invalid content" > invalid.txt
response=$(curl -s -w "%{http_code}" -X POST "$ORCHESTRATOR_URL/ocr/image" -F "image=@invalid.txt" -F "backend=deepseek-ocr")
http_code=${response: -3}
rm invalid.txt

if [ "$http_code" = "400" ] || [ "$http_code" = "500" ]; then
    print_status "PASS" "Invalid image correctly handled (HTTP $http_code)"
else
    print_status "FAIL" "Invalid image should return error but got HTTP $http_code"
fi

# Test 10: Test performance metrics
print_status "INFO" "Test 10: Performance Metrics"
if [ -f "$TEST_IMAGE" ]; then
    response=$(curl -s "$ORCHESTRATOR_URL/ocr/image" -X POST -F "image=@$TEST_IMAGE" -F "backend=deepseek-ocr")

    # Extract processing time
    processing_time=$(echo "$response" | grep -o '"processing_time":[0-9.]*' | cut -d':' -f2)

    if [ -n "$processing_time" ]; then
        print_status "PASS" "Processing time recorded: ${processing_time}s"
    else
        print_status "FAIL" "Processing time not found in response"
    fi
else
    print_status "WARN" "Test image not found, skipping performance test"
fi

echo -e "\n${BLUE}Phase 3 Web Client Test Summary${NC}"
echo "=================================="
print_status "INFO" "All Phase 3 web client functionality tests completed."
print_status "INFO" "Next: Deploy to server and test the actual web interface."

# Instructions for manual web client testing
echo -e "\n${YELLOW}Manual Web Client Testing Instructions:${NC}"
echo "1. Start the web client: cd web-client && npm start"
echo "2. Open browser to: http://localhost:3000"
echo "3. Test backend selection dropdown"
echo "4. Test comparison mode (select 'Compare All Backends')"
echo "5. Verify performance metrics display"
echo "6. Test unified response handling across all tabs"

echo -e "\n${GREEN}Phase 3 Web Client Test Suite Complete${NC}"