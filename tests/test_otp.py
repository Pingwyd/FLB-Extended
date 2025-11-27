import pytest
import json
from unittest.mock import patch

def test_otp_flow(client):
    # 1. Register User
    user_res = client.post('/register', json={
        'full_name': 'OTP User',
        'email': 'otp@example.com',
        'password': 'Password123!',
        'account_type': 'farmer'
    })
    assert user_res.status_code == 201
    
    # Verify initial state
    login_res = client.post('/login', json={
        'email': 'otp@example.com',
        'password': 'Password123!'
    })
    assert login_res.json['email_verified'] == False

    # 2. Request OTP
    # We need to capture the printed OTP or mock the random generation to know what it is.
    # Since we can't easily capture stdout in this test setup without capsys (which is tricky with client fixture),
    # we will mock the random.randint to return a fixed value.
    
    with patch('random.randint', return_value=123456):
        req_res = client.post('/auth/request-otp', json={
            'email': 'otp@example.com'
        })
        assert req_res.status_code == 200
        assert req_res.json['message'] == 'OTP sent to email'

    # 3. Verify with Wrong OTP
    verify_res = client.post('/auth/verify-otp', json={
        'email': 'otp@example.com',
        'otp': '000000'
    })
    assert verify_res.status_code == 400
    assert verify_res.json['error'] == 'Invalid OTP'

    # 4. Verify with Correct OTP
    verify_res = client.post('/auth/verify-otp', json={
        'email': 'otp@example.com',
        'otp': '123456'
    })
    assert verify_res.status_code == 200
    assert verify_res.json['message'] == 'Email verified successfully'

    # 5. Verify User State Updated
    login_res = client.post('/login', json={
        'email': 'otp@example.com',
        'password': 'Password123!'
    })
    assert login_res.json['email_verified'] == True

    # 6. Request OTP again (should say already verified)
    req_res = client.post('/auth/request-otp', json={
        'email': 'otp@example.com'
    })
    assert req_res.status_code == 200
    assert req_res.json['message'] == 'Email already verified'
