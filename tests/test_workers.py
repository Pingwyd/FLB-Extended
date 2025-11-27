"""
Tests for worker marketplace functionality
"""
import pytest


def test_create_worker_profile(client):
    """Test creating a worker profile"""
    # Create a worker user
    user_data = {
        "full_name": "Alice Worker",
        "email": "alice.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    # Create worker profile
    profile_data = {
        "user_id": user_id,
        "specialization": "fumigation",
        "bio": "Professional fumigation specialist with 5 years experience",
        "experience_years": 5,
        "skills": ["pesticide application", "safety protocols", "equipment maintenance"],
        "hourly_rate": 5000.0,  # 5,000 NGN per hour
        "daily_rate": 30000.0,  # 30,000 NGN per day
        "location_state": "Ogun",
        "location_area": "Abeokuta",
        "willing_to_travel": True
    }
    
    r = client.post('/workers/create-profile', json=profile_data)
    assert r.status_code == 201
    
    data = r.get_json()
    assert data['user_id'] == user_id
    assert data['specialization'] == 'fumigation'
    assert data['bio'] == "Professional fumigation specialist with 5 years experience"
    assert data['experience_years'] == 5
    assert data['skills'] == ["pesticide application", "safety protocols", "equipment maintenance"]
    assert data['hourly_rate'] == 5000.0
    assert data['available'] is True
    assert 'id' in data


def test_create_worker_profile_missing_fields(client):
    """Test creating worker profile with missing fields"""
    incomplete_data = {
        "user_id": 1
        # Missing specialization
    }
    
    r = client.post('/workers/create-profile', json=incomplete_data)
    assert r.status_code == 400
    assert 'missing required fields' in r.get_json()['error']


def test_create_worker_profile_invalid_specialization(client):
    """Test creating worker profile with invalid specialization"""
    # Create user first
    user_data = {
        "full_name": "Bob Worker",
        "email": "bob.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    profile_data = {
        "user_id": user_id,
        "specialization": "invalid_spec"
    }
    
    r = client.post('/workers/create-profile', json=profile_data)
    assert r.status_code == 400
    assert 'Invalid specialization' in r.get_json()['error']


def test_create_duplicate_worker_profile(client):
    """Test that a user can only have one worker profile"""
    # Create user
    user_data = {
        "full_name": "Charlie Worker",
        "email": "charlie.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    # Create first profile
    profile_data = {
        "user_id": user_id,
        "specialization": "labor"
    }
    r = client.post('/workers/create-profile', json=profile_data)
    assert r.status_code == 201
    
    # Try to create second profile
    r = client.post('/workers/create-profile', json=profile_data)
    assert r.status_code == 409
    assert 'already exists' in r.get_json()['error']


def test_get_all_workers(client):
    """Test retrieving all worker profiles"""
    # Create multiple workers
    for i in range(3):
        user_data = {
            "full_name": f"Worker {i}",
            "email": f"worker{i}@test.com",
            "password": "Password123",
            "account_type": "worker"
        }
        r = client.post('/register', json=user_data)
        user_id = r.get_json()['id']
        
        profile_data = {
            "user_id": user_id,
            "specialization": "labor" if i % 2 == 0 else "fumigation"
        }
        client.post('/workers/create-profile', json=profile_data)
    
    # Get all workers
    r = client.get('/workers')
    assert r.status_code == 200
    
    data = r.get_json()
    assert len(data) >= 3


def test_get_workers_with_filters(client):
    """Test filtering workers by specialization"""
    # Create workers with different specializations
    specs = ["fumigation", "fertilizer", "labor"]
    for i, spec in enumerate(specs):
        user_data = {
            "full_name": f"Worker {spec}",
            "email": f"{spec}.worker@test.com",
            "password": "Password123",
            "account_type": "worker"
        }
        r = client.post('/register', json=user_data)
        user_id = r.get_json()['id']
        
        profile_data = {
            "user_id": user_id,
            "specialization": spec,
            "location_state": "Lagos" if i < 2 else "Ogun"
        }
        client.post('/workers/create-profile', json=profile_data)
    
    # Filter by specialization
    r = client.get('/workers?specialization=fumigation')
    assert r.status_code == 200
    
    data = r.get_json()
    assert all(w['specialization'] == 'fumigation' for w in data if 'specialization' in w)
    
    # Filter by location
    r = client.get('/workers?location_state=Lagos')
    assert r.status_code == 200
    
    data = r.get_json()
    assert all(w['location_state'] == 'Lagos' for w in data if w['location_state'])


def test_get_workers_availability_filter(client):
    """Test filtering workers by availability"""
    # Create available and unavailable workers
    for i in range(2):
        user_data = {
            "full_name": f"Worker Avail{i}",
            "email": f"avail{i}.worker@test.com",
            "password": "Password123",
            "account_type": "worker"
        }
        r = client.post('/register', json=user_data)
        user_id = r.get_json()['id']
        
        profile_data = {
            "user_id": user_id,
            "specialization": "labor",
            "available": i == 0  # First one available, second not
        }
        client.post('/workers/create-profile', json=profile_data)
    
    # Filter by availability
    r = client.get('/workers?available=true')
    assert r.status_code == 200
    
    data = r.get_json()
    # Should have at least one available worker
    assert any(w['available'] is True for w in data)


def test_get_single_worker(client):
    """Test retrieving a single worker profile"""
    # Create worker
    user_data = {
        "full_name": "Diana Worker",
        "email": "diana.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    profile_data = {
        "user_id": user_id,
        "specialization": "specialist",
        "bio": "Expert in crop diseases"
    }
    
    r = client.post('/workers/create-profile', json=profile_data)
    worker_id = r.get_json()['id']
    
    # Get the worker
    r = client.get(f'/workers/{worker_id}')
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['id'] == worker_id
    assert data['bio'] == "Expert in crop diseases"


def test_get_nonexistent_worker(client):
    """Test retrieving a nonexistent worker"""
    r = client.get('/workers/9999')
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']


def test_update_worker_profile(client):
    """Test updating a worker profile"""
    # Create worker
    user_data = {
        "full_name": "Eve Worker",
        "email": "eve.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    profile_data = {
        "user_id": user_id,
        "specialization": "labor",
        "hourly_rate": 300000
    }
    
    r = client.post('/workers/create-profile', json=profile_data)
    worker_id = r.get_json()['id']
    
    # Update the profile
    update_data = {
        "user_id": user_id,
        "bio": "Updated bio",
        "hourly_rate": 400000,
        "available": False,
        "skills": ["digging", "planting", "weeding"]
    }
    
    r = client.put(f'/workers/{worker_id}', json=update_data)
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['bio'] == "Updated bio"
    assert data['hourly_rate'] == 400000
    assert data['available'] is False
    assert data['skills'] == ["digging", "planting", "weeding"]


def test_update_worker_unauthorized(client):
    """Test that non-owners cannot update a worker profile"""
    # Create two users
    user1_data = {
        "full_name": "Frank Worker",
        "email": "frank.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    user2_data = {
        "full_name": "George Worker",
        "email": "george.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    
    r1 = client.post('/register', json=user1_data)
    r2 = client.post('/register', json=user2_data)
    
    user1_id = r1.get_json()['id']
    user2_id = r2.get_json()['id']
    
    # User1 creates profile
    profile_data = {
        "user_id": user1_id,
        "specialization": "labor"
    }
    
    r = client.post('/workers/create-profile', json=profile_data)
    worker_id = r.get_json()['id']
    
    # User2 tries to update User1's profile
    update_data = {
        "user_id": user2_id,
        "bio": "Hacked bio"
    }
    
    r = client.put(f'/workers/{worker_id}', json=update_data)
    assert r.status_code == 403
    assert 'unauthorized' in r.get_json()['error']


def test_get_worker_by_user_id(client):
    """Test retrieving worker profile by user ID"""
    # Create worker
    user_data = {
        "full_name": "Helen Worker",
        "email": "helen.worker@test.com",
        "password": "Password123",
        "account_type": "worker"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    profile_data = {
        "user_id": user_id,
        "specialization": "irrigation",
        "experience_years": 8
    }
    
    client.post('/workers/create-profile', json=profile_data)
    
    # Get worker by user ID
    r = client.get(f'/workers/user/{user_id}')
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['user_id'] == user_id
    assert data['specialization'] == 'irrigation'
    assert data['experience_years'] == 8


def test_get_worker_by_nonexistent_user(client):
    """Test retrieving worker profile for user without profile"""
    r = client.get('/workers/user/9999')
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']
