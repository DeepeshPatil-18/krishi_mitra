#!/usr/bin/env python
"""Test runner script for verification"""

import sys
import subprocess

print("=" * 60)
print("KRISHIMITRA BACKEND - TEST RUNNER")
print("=" * 60)

# Test 1: Check imports
print("\n[1/4] Checking application imports...")
try:
    from app.main import app
    print("✓ Application imports successfully")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test 2: Run unit tests
print("\n[2/4] Running existing unit tests...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_advisory_engine.py", "tests/test_intent_router.py", "-v"],
        capture_output=True,
        text=True,
        cwd="."
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Warnings (non-fatal):\n{result.stderr}")
except Exception as e:
    print(f"Warning: Could not run unit tests: {e}")

# Test 3: Run API integration tests
print("\n[3/4] Running API integration tests...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_api_integration.py", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd="."
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error output:\n{result.stderr}")
        print(f"Return code: {result.returncode}")
except Exception as e:
    print(f"Error running API tests: {e}")

# Test 4: Verify application starts
print("\n[4/4] Verifying application structure...")
try:
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    if response.status_code == 200:
        print("✓ Health endpoint works")
    else:
        print(f"✗ Health endpoint returned {response.status_code}")
    
    # Test docs
    response = client.get("/docs")
    if response.status_code == 200:
        print("✓ Swagger docs endpoint works")
    else:
        print(f"✗ Docs endpoint returned {response.status_code}")
    
    # Test OpenAPI schema
    response = client.get("/openapi.json")
    if response.status_code == 200:
        print("✓ OpenAPI schema endpoint works")
    else:
        print(f"✗ OpenAPI schema returned {response.status_code}")
    
    # Test intent detection
    response = client.post(
        "/api/v1/intent/detect",
        json={"message": "Where can I sell honey?", "language": "english"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Intent detection works (detected: {data['intent']})")
    else:
        print(f"✗ Intent detection returned {response.status_code}")
    
    # Test advisory
    response = client.post(
        "/api/v1/advisory/recommend",
        json={
            "budget_rupees": 50000,
            "land_size_hectares": 2.0,
            "state": "maharashtra"
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Advisory endpoint works ({len(data['recommendations'])} recommendations)")
    else:
        print(f"✗ Advisory endpoint returned {response.status_code}")
    
    # Test assistant chat
    response = client.post(
        "/api/v1/assistant/chat",
        json={
            "message": "I have 50000 rupees. What can I start?",
            "language": "english"
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Assistant chat works (intent: {data['intent']})")
    else:
        print(f"✗ Assistant chat returned {response.status_code}")

except Exception as e:
    print(f"✗ Application verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST RUNNER COMPLETE")
print("=" * 60)
