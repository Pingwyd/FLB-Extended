import json


def test_register_login_flow(client):
    # Register
    payload = {
        'full_name': 'Test Farmer',
        'email': 'farmer@example.com',
        'password': 's3cretP@ss',
        'account_type': 'farmer'
    }
    rv = client.post('/register', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['email'] == payload['email']

    # Login success
    rv = client.post('/login', data=json.dumps({'email': payload['email'], 'password': payload['password']}), content_type='application/json')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['email'] == payload['email']


def test_register_duplicate_email(client):
    payload = {
        'full_name': 'Another',
        'email': 'dup@example.com',
        'password': 'StrongPass1',
        'account_type': 'worker'
    }
    rv = client.post('/register', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 201

    rv = client.post('/register', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 409


def test_login_wrong_password(client):
    payload = {
        'full_name': 'WrongPass',
        'email': 'wrong@example.com',
        'password': 'StrongPass1',
        'account_type': 'worker'
    }
    rv = client.post('/register', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 201

    rv = client.post('/login', data=json.dumps({'email': payload['email'], 'password': 'badpass'}), content_type='application/json')
    assert rv.status_code == 401


def test_register_invalid_role(client):
    """Test that invalid account_type is rejected"""
    payload = {
        'full_name': 'Invalid Role User',
        'email': 'invalid@example.com',
        'password': 'StrongPass1',
        'account_type': 'invalid_role'
    }
    rv = client.post('/register', data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 400
    data = rv.get_json()
    assert 'Invalid account_type' in data['error']
