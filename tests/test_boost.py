import pytest
import json
from unittest.mock import patch

def test_boost_listing(client):
    # 1. Create User
    user_res = client.post('/register', json={
        'full_name': 'Booster User',
        'email': 'booster@example.com',
        'password': 'Password123!',
        'account_type': 'farmer'
    })
    assert user_res.status_code == 201, f"Register failed: {user_res.json}"
    # Login to get user details (or just assume ID 1 if it's the first user, but better to check)
    login_res = client.post('/login', json={
        'email': 'booster@example.com',
        'password': 'Password123!'
    })
    assert login_res.status_code == 200
    user_id = login_res.json['id']

    # 2. Fund Wallet
    fund_res = client.post('/api/wallet/fund', json={
        'user_id': user_id,
        'amount': 10000,
        'email': 'booster@example.com'
    })
    assert fund_res.status_code == 200
    txn_ref = fund_res.json['txn_ref']

    # Mock Interswitch verification
    with patch('app.requests.get') as mock_get:
        # Fee is 1.5% of 10000 = 150. Total = 10150.
        # Amount in kobo = 1015000
        mock_get.return_value.json.return_value = {
            'ResponseCode': '00',
            'Amount': '1015000' 
        }
        client.get(f'/api/payment/callback?txn_ref={txn_ref}')

    # Verify balance
    bal_res = client.get(f'/api/wallet/balance/{user_id}')
    assert bal_res.json['balance'] == 10000.0

    # 3. Create Listing
    listing_res = client.post('/listings/create', json={
        'owner_id': user_id,
        'title': 'Test Listing',
        'description': 'A test listing',
        'price': 1000,
        'listing_type': 'land_sale',
        'location_state': 'Lagos'
    })
    assert listing_res.status_code == 201
    listing_id = listing_res.json['id']

    # 4. Boost Listing
    boost_res = client.post(f'/listings/{listing_id}/boost', json={
        'user_id': user_id
    })
    assert boost_res.status_code == 200
    assert boost_res.json['message'] == 'Listing boosted successfully'
    assert 'boost_expiry' in boost_res.json
    assert boost_res.json['new_balance'] == 5000.0

    # 5. Verify Listing is Boosted
    list_res = client.get('/listings')
    listings = list_res.json
    assert len(listings) > 0
    assert listings[0]['id'] == listing_id
    assert listings[0]['featured'] == True
    assert listings[0]['boost_expiry'] is not None

def test_boost_worker_profile(client):
    # 1. Create User
    user_res = client.post('/register', json={
        'full_name': 'Worker User',
        'email': 'worker@example.com',
        'password': 'Password123!',
        'account_type': 'worker'
    })
    assert user_res.status_code == 201
    # Login
    login_res = client.post('/login', json={
        'email': 'worker@example.com',
        'password': 'Password123!'
    })
    user_id = login_res.json['id']

    # 2. Fund Wallet
    fund_res = client.post('/api/wallet/fund', json={
        'user_id': user_id,
        'amount': 10000,
        'email': 'worker@example.com'
    })
    txn_ref = fund_res.json['txn_ref']

    with patch('app.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'ResponseCode': '00',
            'Amount': '1015000' 
        }
        client.get(f'/api/payment/callback?txn_ref={txn_ref}')

    # 3. Create Worker Profile
    profile_res = client.post('/workers/create-profile', json={
        'user_id': user_id,
        'specialization': 'labor',
        'hourly_rate': 500
    })
    assert profile_res.status_code == 201
    worker_id = profile_res.json['id']
    
    # 4. Boost Worker
    boost_res = client.post(f'/workers/{worker_id}/boost', json={
        'user_id': user_id
    })
    assert boost_res.status_code == 200
    assert boost_res.json['message'] == 'Worker profile boosted successfully'
    assert 'boost_expiry' in boost_res.json
    assert boost_res.json['new_balance'] == 5000.0

    # 5. Verify Worker is Boosted
    workers_res = client.get('/workers')
    workers = workers_res.json
    assert len(workers) > 0
    assert workers[0]['id'] == worker_id
    assert workers[0]['is_boosted'] == True
    assert workers[0]['boost_expiry'] is not None
