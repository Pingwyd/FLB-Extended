"""
Tests for contract functionality
"""
import pytest


def test_create_contract(client):
    """Test creating a contract between two parties"""
    # Create two users
    farmer_data = {
        "full_name": "Alice Farmer",
        "email": "alice.contract@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    realtor_data = {
        "full_name": "Bob Realtor",
        "email": "bob.contract@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    
    r1 = client.post('/register', json=farmer_data)
    r2 = client.post('/register', json=realtor_data)
    
    farmer_id = r1.get_json()['id']
    realtor_id = r2.get_json()['id']
    
    # Create a contract
    contract_data = {
        "title": "Farm Land Lease Agreement",
        "description": "Lease of 5 hectares of farmland",
        "party_a_id": farmer_id,
        "party_b_id": realtor_id,
        "terms": "Party A agrees to lease land from Party B for 12 months at 500,000 NGN per month.",
        "amount": 6000000.0  # 6,000,000 NGN
    }
    
    r = client.post('/contracts/create', json=contract_data)
    assert r.status_code == 201
    
    data = r.get_json()
    assert data['title'] == "Farm Land Lease Agreement"
    assert data['party_a_id'] == farmer_id
    assert data['party_b_id'] == realtor_id
    assert data['status'] == 'draft'
    assert data['party_a_signed'] is False
    assert data['party_b_signed'] is False
    assert 'id' in data
    assert 'created_at' in data


def test_create_contract_missing_fields(client):
    """Test creating a contract with missing required fields"""
    incomplete_data = {
        "title": "Test Contract",
        "party_a_id": 1
        # Missing party_b_id and terms
    }
    
    r = client.post('/contracts/create', json=incomplete_data)
    assert r.status_code == 400
    assert 'missing required fields' in r.get_json()['error']


def test_create_contract_nonexistent_party(client):
    """Test creating a contract with nonexistent party"""
    contract_data = {
        "title": "Invalid Contract",
        "party_a_id": 999,
        "party_b_id": 1000,
        "terms": "Test terms"
    }
    
    r = client.post('/contracts/create', json=contract_data)
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']


def test_sign_contract_single_party(client):
    """Test one party signing a contract"""
    # Create two users
    farmer_data = {
        "full_name": "Charlie Farmer",
        "email": "charlie.contract@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    worker_data = {
        "full_name": "Diana Worker",
        "email": "diana.contract@test.com",
        "password": "Pass123",
        "account_type": "worker"
    }
    
    r1 = client.post('/register', json=farmer_data)
    r2 = client.post('/register', json=worker_data)
    
    farmer_id = r1.get_json()['id']
    worker_id = r2.get_json()['id']
    
    # Create a contract
    contract_data = {
        "title": "Farm Work Agreement",
        "party_a_id": farmer_id,
        "party_b_id": worker_id,
        "terms": "Worker will provide fumigation services for 3 days."
    }
    
    contract_response = client.post('/contracts/create', json=contract_data)
    contract_id = contract_response.get_json()['id']
    
    # Party A signs
    r = client.post(f'/contracts/{contract_id}/sign', json={"user_id": farmer_id})
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['party_a_signed'] is True
    assert data['party_a_signed_at'] is not None
    assert data['party_b_signed'] is False
    assert data['status'] == 'draft'  # Still draft until both sign


def test_sign_contract_both_parties(client):
    """Test both parties signing a contract"""
    # Create two users
    farmer_data = {
        "full_name": "Eve Farmer",
        "email": "eve.contract@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    realtor_data = {
        "full_name": "Frank Realtor",
        "email": "frank.contract@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    
    r1 = client.post('/register', json=farmer_data)
    r2 = client.post('/register', json=realtor_data)
    
    farmer_id = r1.get_json()['id']
    realtor_id = r2.get_json()['id']
    
    # Create a contract
    contract_data = {
        "title": "Land Purchase Agreement",
        "party_a_id": farmer_id,
        "party_b_id": realtor_id,
        "terms": "Transfer of land ownership for 10,000,000 NGN.",
        "amount": 1000000000  # 10,000,000 NGN in kobo
    }
    
    contract_response = client.post('/contracts/create', json=contract_data)
    contract_id = contract_response.get_json()['id']
    
    # Both parties sign
    client.post(f'/contracts/{contract_id}/sign', json={"user_id": farmer_id})
    r = client.post(f'/contracts/{contract_id}/sign', json={"user_id": realtor_id})
    
    assert r.status_code == 200
    data = r.get_json()
    assert data['party_a_signed'] is True
    assert data['party_b_signed'] is True
    assert data['party_b_signed_at'] is not None
    assert data['status'] == 'signed'  # Now fully signed


def test_sign_contract_unauthorized_user(client):
    """Test a user who is not a party trying to sign a contract"""
    # Create three users
    farmer_data = {
        "full_name": "George Farmer",
        "email": "george.contract@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    realtor_data = {
        "full_name": "Helen Realtor",
        "email": "helen.contract@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    outsider_data = {
        "full_name": "Ivan Outsider",
        "email": "ivan.contract@test.com",
        "password": "Pass123",
        "account_type": "worker"
    }
    
    r1 = client.post('/register', json=farmer_data)
    r2 = client.post('/register', json=realtor_data)
    r3 = client.post('/register', json=outsider_data)
    
    farmer_id = r1.get_json()['id']
    realtor_id = r2.get_json()['id']
    outsider_id = r3.get_json()['id']
    
    # Create a contract
    contract_data = {
        "title": "Private Agreement",
        "party_a_id": farmer_id,
        "party_b_id": realtor_id,
        "terms": "Private terms between farmer and realtor."
    }
    
    contract_response = client.post('/contracts/create', json=contract_data)
    contract_id = contract_response.get_json()['id']
    
    # Outsider tries to sign
    r = client.post(f'/contracts/{contract_id}/sign', json={"user_id": outsider_id})
    assert r.status_code == 403
    assert 'not a party' in r.get_json()['error']


def test_get_user_contracts(client):
    """Test retrieving all contracts for a user"""
    # Create users
    farmer_data = {
        "full_name": "Jane Farmer",
        "email": "jane.contract@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    realtor_data = {
        "full_name": "Karl Realtor",
        "email": "karl.contract@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    worker_data = {
        "full_name": "Linda Worker",
        "email": "linda.contract@test.com",
        "password": "Pass123",
        "account_type": "worker"
    }
    
    r1 = client.post('/register', json=farmer_data)
    r2 = client.post('/register', json=realtor_data)
    r3 = client.post('/register', json=worker_data)
    
    farmer_id = r1.get_json()['id']
    realtor_id = r2.get_json()['id']
    worker_id = r3.get_json()['id']
    
    # Create multiple contracts with farmer as party
    contract1 = {
        "title": "Contract 1",
        "party_a_id": farmer_id,
        "party_b_id": realtor_id,
        "terms": "Terms 1"
    }
    contract2 = {
        "title": "Contract 2",
        "party_a_id": worker_id,
        "party_b_id": farmer_id,
        "terms": "Terms 2"
    }
    
    client.post('/contracts/create', json=contract1)
    client.post('/contracts/create', json=contract2)
    
    # Get contracts for farmer
    r = client.get(f'/contracts/{farmer_id}')
    assert r.status_code == 200
    
    contracts = r.get_json()
    assert len(contracts) == 2
    assert any(c['title'] == 'Contract 1' for c in contracts)
    assert any(c['title'] == 'Contract 2' for c in contracts)


def test_sign_nonexistent_contract(client):
    """Test signing a nonexistent contract"""
    r = client.post('/contracts/9999/sign', json={"user_id": 1})
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']
