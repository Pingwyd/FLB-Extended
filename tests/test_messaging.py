"""
Tests for messaging functionality
"""
import pytest


def test_send_message(client):
    """Test sending a message between users"""
    # Create two users
    user1_data = {
        "full_name": "Alice Farmer",
        "email": "alice@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    user2_data = {
        "full_name": "Bob Worker",
        "email": "bob@test.com",
        "password": "Pass123",
        "account_type": "worker"
    }
    
    r1 = client.post('/register', json=user1_data)
    r2 = client.post('/register', json=user2_data)
    
    user1_id = r1.get_json()['id']
    user2_id = r2.get_json()['id']
    
    # Send a message
    message_data = {
        "sender_id": user1_id,
        "recipient_id": user2_id,
        "subject": "Job Opportunity",
        "content": "Hello, I need help with my farm."
    }
    
    r = client.post('/messages/send', json=message_data)
    assert r.status_code == 201
    
    data = r.get_json()
    assert data['sender_id'] == user1_id
    assert data['recipient_id'] == user2_id
    assert data['subject'] == "Job Opportunity"
    assert data['content'] == "Hello, I need help with my farm."
    assert data['read'] is False
    assert 'id' in data
    assert 'created_at' in data


def test_send_message_missing_fields(client):
    """Test sending a message with missing fields"""
    incomplete_data = {
        "sender_id": 1,
        "content": "Test"
        # Missing recipient_id
    }
    
    r = client.post('/messages/send', json=incomplete_data)
    assert r.status_code == 400
    assert 'missing required fields' in r.get_json()['error']


def test_send_message_nonexistent_user(client):
    """Test sending a message to a nonexistent user"""
    message_data = {
        "sender_id": 999,
        "recipient_id": 1000,
        "content": "Test message"
    }
    
    r = client.post('/messages/send', json=message_data)
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']


def test_get_user_messages(client):
    """Test retrieving messages for a user"""
    # Create two users
    user1_data = {
        "full_name": "Charlie Farmer",
        "email": "charlie@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    user2_data = {
        "full_name": "Diana Realtor",
        "email": "diana@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    
    r1 = client.post('/register', json=user1_data)
    r2 = client.post('/register', json=user2_data)
    
    user1_id = r1.get_json()['id']
    user2_id = r2.get_json()['id']
    
    # Send messages in both directions
    msg1 = {
        "sender_id": user1_id,
        "recipient_id": user2_id,
        "content": "Hello from Charlie"
    }
    msg2 = {
        "sender_id": user2_id,
        "recipient_id": user1_id,
        "content": "Hi Charlie, this is Diana"
    }
    
    client.post('/messages/send', json=msg1)
    client.post('/messages/send', json=msg2)
    
    # Get messages for user1
    r = client.get(f'/messages/{user1_id}')
    assert r.status_code == 200
    
    data = r.get_json()
    assert 'sent' in data
    assert 'received' in data
    assert len(data['sent']) == 1
    assert len(data['received']) == 1
    assert data['sent'][0]['content'] == "Hello from Charlie"
    assert data['received'][0]['content'] == "Hi Charlie, this is Diana"


def test_mark_message_read(client):
    """Test marking a message as read"""
    # Create two users
    user1_data = {
        "full_name": "Eve Farmer",
        "email": "eve@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    user2_data = {
        "full_name": "Frank Worker",
        "email": "frank@test.com",
        "password": "Pass123",
        "account_type": "worker"
    }
    
    r1 = client.post('/register', json=user1_data)
    r2 = client.post('/register', json=user2_data)
    
    user1_id = r1.get_json()['id']
    user2_id = r2.get_json()['id']
    
    # Send a message
    message_data = {
        "sender_id": user1_id,
        "recipient_id": user2_id,
        "content": "Test message"
    }
    
    msg_response = client.post('/messages/send', json=message_data)
    message_id = msg_response.get_json()['id']
    
    # Mark as read
    r = client.put(f'/messages/{message_id}/read')
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['read'] is True
    assert data['read_at'] is not None


def test_mark_nonexistent_message_read(client):
    """Test marking a nonexistent message as read"""
    r = client.put('/messages/9999/read')
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']
