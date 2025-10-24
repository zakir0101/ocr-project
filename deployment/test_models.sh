#!/bin/bash

# Model Validation Test Script
# This script validates that models have been downloaded into their respective directories

set -e  # Exit on any error

echo "=========================================="
echo "Model Validation Test"
echo "=========================================="

# Function to check model directory
check_model_directory() {
    local name=$1
    local model_dir=$2
    local expected_files=$3

    echo ""
    echo "🧪 Checking $name model directory..."
    echo "   Directory: $model_dir"

    if [ -d "$model_dir" ]; then
        echo "   ✅ Directory exists"

        # Check if directory is empty
        if [ "$(ls -A "$model_dir")" ]; then
            echo "   ✅ Directory is not empty"

            # List files
            echo "   📁 Files found:"
            find "$model_dir" -type f | head -10 | while read file; do
                echo "      - $(basename "$file") ($(du -h "$file" | cut -f1))"
            done

            # Count total files
            file_count=$(find "$model_dir" -type f | wc -l)
            echo "   📊 Total files: $file_count"

            return 0
        else
            echo "   ❌ Directory is empty"
            return 1
        fi
    else
        echo "   ❌ Directory does not exist"
        return 1
    fi
}

# Function to check for specific model files
check_model_files() {
    local name=$1
    local model_dir=$2

    echo ""
    echo "🧪 Checking $name model files..."

    # Common model file patterns
    common_files=(
        "config.json"
        "*.safetensors"
        "*.bin"
        "*.pt"
        "tokenizer.json"
        "tokenizer_config.json"
        "vocab.json"
        "special_tokens_map.json"
    )

    found_files=0
    for pattern in "${common_files[@]}"; do
        if find "$model_dir" -name "$pattern" | grep -q .; then
            found_files=$((found_files + 1))
            echo "   ✅ Found files matching: $pattern"
        fi
    done

    if [ $found_files -gt 0 ]; then
        echo "   ✅ Found $found_files types of model files"
        return 0
    else
        echo "   ❌ No common model files found"
        return 1
    fi
}

# Main test sequence

# Check DeepSeek model directory
DEEPSEEK_MODEL_DIR="../models/deepseek-ocr"
check_model_directory "DeepSeek" "$DEEPSEEK_MODEL_DIR"
check_model_files "DeepSeek" "$DEEPSEEK_MODEL_DIR"

# Check Mineru model directory
MINERU_MODEL_DIR="../models/mineru"
check_model_directory "Mineru" "$MINERU_MODEL_DIR"
check_model_files "Mineru" "$MINERU_MODEL_DIR"

echo ""
echo "=========================================="
echo "✅ Model Validation Summary"
echo "=========================================="
echo ""
echo "📊 Results:"
echo "   - DeepSeek model: $DEEPSEEK_MODEL_DIR"
echo "   - Mineru model: $MINERU_MODEL_DIR"
echo ""
echo "🎯 Success Criteria:"
echo "   ✓ Model directories exist"
echo "   ✓ Model directories are not empty"
echo "   ✓ Common model files are present"
echo ""
echo "⚠️  Note: Mineru models may be downloaded on first use"
echo "=========================================="