#!/bin/bash

# Virtual Environment Validation Test Script
# This script validates that virtual environments are properly set up for each module

set -e  # Exit on any error

echo "=========================================="
echo "Virtual Environment Validation Test"
echo "=========================================="

# Function to check virtual environment
check_venv() {
    local name=$1
    local venv_dir=$2

    echo ""
    echo "🧪 Checking $name virtual environment..."
    echo "   Directory: $venv_dir"

    if [ -d "$venv_dir" ]; then
        echo "   ✅ Virtual environment directory exists"

        # Check for Python executable
        if [ -f "$venv_dir/bin/python" ]; then
            echo "   ✅ Python executable found"

            # Check Python version
            python_version=$("$venv_dir/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
            echo "   📊 Python version: $python_version"

            # Check pip
            if [ -f "$venv_dir/bin/pip" ]; then
                echo "   ✅ pip found"

                # Check if environment is activated properly
                if [ -n "$VIRTUAL_ENV" ]; then
                    echo "   ✅ Virtual environment is activated"
                else
                    echo "   ℹ️  Virtual environment not activated (expected for static test)"
                fi

                return 0
            else
                echo "   ❌ pip not found"
                return 1
            fi
        else
            echo "   ❌ Python executable not found"
            return 1
        fi
    else
        echo "   ❌ Virtual environment directory does not exist"
        return 1
    fi
}

# Function to check key dependencies
check_dependencies() {
    local name=$1
    local venv_dir=$2
    local requirements_file=$3

    echo ""
    echo "🧪 Checking $name dependencies..."

    # Activate virtual environment temporarily
    source "$venv_dir/bin/activate"

    # Check if requirements file exists
    if [ -f "$requirements_file" ]; then
        echo "   ✅ Requirements file exists: $(basename "$requirements_file")"

        # Check key dependencies
        key_deps=("flask" "torch" "Pillow")

        for dep in "${key_deps[@]}"; do
            if python -c "import $dep" 2>/dev/null; then
                dep_version=$(python -c "import $dep; print($dep.__version__)" 2>/dev/null || echo "unknown")
                echo "   ✅ $dep: $dep_version"
            else
                echo "   ❌ $dep: Not installed"
            fi
        done

        # Check backend-specific dependencies
        if [ "$name" = "DeepSeek" ]; then
            backend_deps=("vllm" "transformers")
        elif [ "$name" = "Mineru" ]; then
            backend_deps=("mineru")
        elif [ "$name" = "Orchestrator" ]; then
            backend_deps=("requests")
        fi

        for dep in "${backend_deps[@]}"; do
            if python -c "import $dep" 2>/dev/null; then
                dep_version=$(python -c "import $dep; print($dep.__version__)" 2>/dev/null || echo "unknown")
                echo "   ✅ $dep: $dep_version"
            else
                echo "   ❌ $dep: Not installed"
            fi
        done

    else
        echo "   ❌ Requirements file not found: $(basename "$requirements_file")"
    fi

    # Deactivate virtual environment
    deactivate
}

# Main test sequence

# Check DeepSeek virtual environment
DEEPSEEK_VENV_DIR="../backends/deepseek-ocr/venv"
DEEPSEEK_REQUIREMENTS="../backends/deepseek-ocr/requirements.txt"
check_venv "DeepSeek" "$DEEPSEEK_VENV_DIR"
check_dependencies "DeepSeek" "$DEEPSEEK_VENV_DIR" "$DEEPSEEK_REQUIREMENTS"

# Check Mineru virtual environment
MINERU_VENV_DIR="../backends/mineru/venv"
MINERU_REQUIREMENTS="../backends/mineru/requirements.txt"
check_venv "Mineru" "$MINERU_VENV_DIR"
check_dependencies "Mineru" "$MINERU_VENV_DIR" "$MINERU_REQUIREMENTS"

# Check orchestrator virtual environment
ORCHESTRATOR_VENV_DIR="../orchestrator/venv"
ORCHESTRATOR_REQUIREMENTS="../orchestrator/requirements.txt"
check_venv "Orchestrator" "$ORCHESTRATOR_VENV_DIR"
check_dependencies "Orchestrator" "$ORCHESTRATOR_VENV_DIR" "$ORCHESTRATOR_REQUIREMENTS"

echo ""
echo "=========================================="
echo "✅ Virtual Environment Validation Summary"
echo "=========================================="
echo ""
echo "📊 Results:"
echo "   - DeepSeek: $DEEPSEEK_VENV_DIR"
echo "   - Mineru: $MINERU_VENV_DIR"
echo "   - Orchestrator: $ORCHESTRATOR_VENV_DIR"
echo ""
echo "🎯 Success Criteria:"
echo "   ✓ Virtual environment directories exist"
echo "   ✓ Python executables are present"
echo "   ✓ pip is available"
echo "   ✓ Key dependencies are installed"
echo ""
echo "⚠️  Note: All environments should be isolated from each other"
echo "=========================================="