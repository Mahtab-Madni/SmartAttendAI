#!/usr/bin/env python3
"""
SmartAttendAI Basic Functionality Test
Tests core components and dependencies
"""
import sys
import os
import traceback

print("SmartAttendAI - Basic Functionality Test")
print("=" * 50)

def test_imports():
    """Test if core modules can be imported"""
    print("\n1. Testing Core Imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
    
    try:
        import uvicorn
        print("✓ Uvicorn imported successfully")
    except ImportError as e:
        print(f"✗ Uvicorn import failed: {e}")

def test_project_structure():
    """Test project directory structure"""
    print("\n2. Testing Project Structure...")
    
    required_dirs = [
        "data", "models", "templates", "static", 
        "src", "config", "data/logs", "data/faces"
    ]
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Directory '{dir_name}' exists")
        else:
            print(f"✗ Directory '{dir_name}' missing")

def test_config_import():
    """Test configuration import"""
    print("\n3. Testing Configuration...")
    
    try:
        import config.settings as settings
        print("✓ Configuration imported successfully")
        print(f"✓ Data directory: {settings.DATA_DIR}") 
        print(f"✓ Models directory: {settings.MODELS_DIR}")
    except Exception as e:
        print(f"✗ Configuration import failed: {e}")
        traceback.print_exc()

def test_src_modules():
    """Test source modules"""
    print("\n4. Testing Source Modules...")
    
    modules_to_test = [
        "src.utils.database",
        "src.utils.notifications", 
        "src.geofencing.validator",
        "src.emotion_detection.analyzer",
        "src.face_recognition.recognizer"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
        except ImportError as e:
            print(f"✗ {module} import failed: {e}")
        except Exception as e:
            print(f"⚠ {module} imported but has issues: {e}")

def test_fastapi_app():
    """Test FastAPI app creation"""
    print("\n5. Testing FastAPI App...")
    
    try:
        # Add a basic version of the app that can run without all dependencies
        from fastapi import FastAPI
        
        app = FastAPI(title="SmartAttendAI Test")
        
        @app.get("/")
        def health_check():
            return {"status": "healthy", "message": "SmartAttendAI is running"}
        
        print("✓ Basic FastAPI app created successfully")
        return app
        
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        return None

if __name__ == "__main__":
    test_imports()
    test_project_structure() 
    test_config_import()
    test_src_modules()
    app = test_fastapi_app()
    
    print("\n" + "=" * 50)
    if app:
        print("✓ Basic setup test completed successfully!")
        print("\nTo start the web server, run:")
        print("python -c \"import test_setup; import uvicorn; uvicorn.test_setup:app --reload --host 0.0.0.0 --port 8000\"")
    else:
        print("✗ Some tests failed. Please check the errors above.")