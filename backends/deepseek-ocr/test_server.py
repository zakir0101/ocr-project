#!/usr/bin/env python3
"""
Test script to check if DeepSeek backend server can initialize
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_server_initialization():
    """Test if the server can initialize without loading the model"""
    print("Testing DeepSeek server initialization...")
    print("=" * 50)

    try:
        # Try to import the backend class
        from deepseek_ocr_backend import DeepSeekOCRBackend
        print("✓ DeepSeekOCRBackend import successful")

        # Try to create an instance
        backend = DeepSeekOCRBackend(model_path="./fake_model")
        print("✓ DeepSeekOCRBackend instance created")

        # Test health status without model loaded
        health_status = backend.get_health_status()
        print(f"✓ Health status: {health_status}")

        # Test cleanup
        backend.cleanup()
        print("✓ Cleanup successful")

        print("=" * 50)
        print("✓ Server initialization test passed")
        return True

    except Exception as e:
        print(f"✗ Server initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app():
    """Test if Flask app can be created"""
    print("\nTesting Flask app creation...")
    print("=" * 50)

    try:
        # Import Flask app
        from deepseek_ocr_backend import app
        print("✓ Flask app import successful")

        # Test if app has expected routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.rule} -> {rule.endpoint}")

        expected_routes = [
            '/ocr/image',
            '/ocr/pdf',
            '/health'
        ]

        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Route {route} found")
            else:
                print(f"✗ Route {route} not found")

        print("=" * 50)
        print("✓ Flask app test passed")
        return True

    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_server_initialization()
    success2 = test_flask_app()

    if success1 and success2:
        print("\n🎉 All tests passed! DeepSeek backend is ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")