"""
Simple script to test registration and login endpoints manually
Run this while the Flask app is running: python test_manual.py
NOT meant to be run via pytest - use tests/ folder for that
"""
import requests
import json
import sys

# Skip this file when running pytest
if 'pytest' in sys.modules:
    import pytest
    pytest.skip("Manual test script, not for pytest", allow_module_level=True)

BASE_URL = "http://localhost:5000"

def test_registration():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    
    payload = {
        "full_name": "John Farmer",
        "email": "john@farm.com",
        "password": "SecurePass123!",
        "account_type": "farmer"
    }
    
    response = requests.post(
        f"{BASE_URL}/register",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        return True
    elif response.status_code == 409:
        print("⚠️  Email already registered (this is okay for testing)")
        return True
    else:
        print("❌ Registration failed")
        return False


def test_login(email, password):
    """Test user login"""
    print("\n=== Testing Login ===")
    
    payload = {
        "email": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/login",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
        return True
    else:
        print("❌ Login failed")
        return False


def test_wrong_password(email):
    """Test login with wrong password"""
    print("\n=== Testing Wrong Password ===")
    
    payload = {
        "email": email,
        "password": "WrongPassword123"
    }
    
    response = requests.post(
        f"{BASE_URL}/login",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected wrong password!")
        return True
    else:
        print("❌ Should have rejected wrong password")
        return False


def list_users():
    """List all registered users"""
    print("\n=== Listing All Users ===")
    
    response = requests.get(f"{BASE_URL}/users")
    
    print(f"Status Code: {response.status_code}")
    users = response.json()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"  - {user['full_name']} ({user['email']}) - {user['account_type']}")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("FLB Extended - Authentication Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    
    # Test registration
    test_registration()
    
    # Test successful login
    test_login("john@farm.com", "SecurePass123!")
    
    # Test wrong password
    test_wrong_password("john@farm.com")
    
    # Register another user
    print("\n=== Registering Another User ===")
    payload2 = {
        "full_name": "Sarah Worker",
        "email": "sarah@work.com",
        "password": "WorkPass456!",
        "account_type": "worker"
    }
    requests.post(f"{BASE_URL}/register", json=payload2)
    
    # List all users
    list_users()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
