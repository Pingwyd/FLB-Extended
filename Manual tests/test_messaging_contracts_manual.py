"""
Manual test script for messaging and contracts workflow
Run this while the Flask app is running
"""
import requests
import json
import sys

# Skip this file when running pytest
if 'pytest' in sys.modules:
    import pytest
    pytest.skip("Manual test script, not for pytest", allow_module_level=True)

BASE_URL = "http://localhost:5000"

print("=" * 70)
print("Messaging & Contracts Workflow Test")
print("=" * 70)

# Step 1: Register users
print("\n1. Registering users...")
farmer = {
    "full_name": "John Farmer",
    "email": "johnfarmer@msg.com",
    "password": "FarmPass123",
    "account_type": "farmer"
}
realtor = {
    "full_name": "Sarah Realtor",
    "email": "sarah@msg.com",
    "password": "RealtorPass123",
    "account_type": "realtor"
}
worker = {
    "full_name": "Mike Worker",
    "email": "mike@msg.com",
    "password": "WorkPass123",
    "account_type": "worker"
}

r = requests.post(f"{BASE_URL}/register", json=farmer)
farmer_id = r.json()['id']
print(f"✅ Farmer registered: ID={farmer_id}")

r = requests.post(f"{BASE_URL}/register", json=realtor)
realtor_id = r.json()['id']
print(f"✅ Realtor registered: ID={realtor_id}")

r = requests.post(f"{BASE_URL}/register", json=worker)
worker_id = r.json()['id']
print(f"✅ Worker registered: ID={worker_id}")

# ========== MESSAGING TESTS ==========
print("\n" + "=" * 70)
print("MESSAGING TESTS")
print("=" * 70)

# Step 2: Send messages
print("\n2. Sending messages...")
msg1 = {
    "sender_id": farmer_id,
    "recipient_id": realtor_id,
    "subject": "Land Inquiry",
    "content": "Hi Sarah, I'm interested in leasing farmland. Do you have any available?"
}
msg2 = {
    "sender_id": realtor_id,
    "recipient_id": farmer_id,
    "subject": "RE: Land Inquiry",
    "content": "Hello John! Yes, I have 10 hectares available in Ogun State."
}
msg3 = {
    "sender_id": farmer_id,
    "recipient_id": worker_id,
    "subject": "Farm Work Opportunity",
    "content": "Hi Mike, I need fumigation services. Are you available next week?"
}

for i, msg in enumerate([msg1, msg2, msg3], 1):
    r = requests.post(f"{BASE_URL}/messages/send", json=msg)
    if r.status_code == 201:
        print(f"✅ Message {i} sent: {msg['subject']}")
    else:
        print(f"❌ Failed to send message {i}: {r.json()}")

# Step 3: Retrieve messages
print("\n3. Retrieving farmer's messages...")
r = requests.get(f"{BASE_URL}/messages/{farmer_id}")
if r.status_code == 200:
    data = r.json()
    print(f"✅ Farmer has {len(data['sent'])} sent messages and {len(data['received'])} received messages")
    print("\n   Sent messages:")
    for msg in data['sent']:
        print(f"   - To User {msg['recipient_id']}: {msg['subject']}")
    print("\n   Received messages:")
    for msg in data['received']:
        print(f"   - From User {msg['sender_id']}: {msg['subject']} (Read: {msg['read']})")
else:
    print(f"❌ Failed to retrieve messages: {r.json()}")

# Step 4: Mark message as read
print("\n4. Marking first message as read...")
r = requests.get(f"{BASE_URL}/messages/{farmer_id}")
received_msgs = r.json()['received']
if received_msgs:
    msg_id = received_msgs[0]['id']
    r = requests.put(f"{BASE_URL}/messages/{msg_id}/read")
    if r.status_code == 200:
        print(f"✅ Message {msg_id} marked as read")
        print(f"   Read at: {r.json()['read_at']}")
    else:
        print(f"❌ Failed to mark message as read: {r.json()}")

# ========== CONTRACT TESTS ==========
print("\n" + "=" * 70)
print("CONTRACT TESTS")
print("=" * 70)

# Step 5: Create a contract
print("\n5. Creating land lease contract...")
contract1 = {
    "title": "Farm Land Lease Agreement",
    "description": "10 hectares farmland in Ogun State",
    "party_a_id": farmer_id,
    "party_b_id": realtor_id,
    "terms": "Party A (Farmer) agrees to lease 10 hectares of land from Party B (Realtor) for 12 months. Monthly rent: 500,000 NGN. Payment due on 1st of each month. Party A is responsible for maintenance and farming activities. Contract begins immediately upon signing.",
    "amount": 6000000.0  # 6,000,000 NGN (12 months × 500,000)
}

r = requests.post(f"{BASE_URL}/contracts/create", json=contract1)
if r.status_code == 201:
    contract1_id = r.json()['id']
    print(f"✅ Contract created: ID={contract1_id}")
    print(f"   Title: {r.json()['title']}")
    print(f"   Status: {r.json()['status']}")
    print(f"   Amount: {r.json()['amount']} NGN")
else:
    print(f"❌ Failed to create contract: {r.json()}")
    sys.exit(1)

# Step 6: Create work contract
print("\n6. Creating worker service contract...")
contract2 = {
    "title": "Fumigation Service Contract",
    "description": "Farm fumigation services",
    "party_a_id": farmer_id,
    "party_b_id": worker_id,
    "terms": "Party B (Worker) will provide professional fumigation services for Party A's 10-hectare farm. Duration: 3 days. Payment: 150,000 NGN upon completion. Worker to provide own equipment and safety gear.",
    "amount": 150000.0  # 150,000 NGN
}

r = requests.post(f"{BASE_URL}/contracts/create", json=contract2)
if r.status_code == 201:
    contract2_id = r.json()['id']
    print(f"✅ Contract created: ID={contract2_id}")
    print(f"   Title: {r.json()['title']}")
else:
    print(f"❌ Failed to create contract: {r.json()}")

# Step 7: Farmer signs first contract
print(f"\n7. Farmer signing contract {contract1_id}...")
r = requests.post(f"{BASE_URL}/contracts/{contract1_id}/sign", json={"user_id": farmer_id})
if r.status_code == 200:
    data = r.json()
    print(f"✅ Farmer signed the contract")
    print(f"   Party A signed: {data['party_a_signed']} at {data['party_a_signed_at']}")
    print(f"   Party B signed: {data['party_b_signed']}")
    print(f"   Status: {data['status']}")
else:
    print(f"❌ Failed to sign contract: {r.json()}")

# Step 8: Realtor signs first contract
print(f"\n8. Realtor signing contract {contract1_id}...")
r = requests.post(f"{BASE_URL}/contracts/{contract1_id}/sign", json={"user_id": realtor_id})
if r.status_code == 200:
    data = r.json()
    print(f"✅ Realtor signed the contract")
    print(f"   Party A signed: {data['party_a_signed']}")
    print(f"   Party B signed: {data['party_b_signed']} at {data['party_b_signed_at']}")
    print(f"   Status: {data['status']} ⭐")
else:
    print(f"❌ Failed to sign contract: {r.json()}")

# Step 9: View farmer's contracts
print(f"\n9. Viewing farmer's contracts...")
r = requests.get(f"{BASE_URL}/contracts/{farmer_id}")
if r.status_code == 200:
    contracts = r.json()
    print(f"✅ Farmer has {len(contracts)} contracts")
    for contract in contracts:
        print(f"\n   Contract ID {contract['id']}: {contract['title']}")
        print(f"   Status: {contract['status']}")
        print(f"   Party A signed: {contract['party_a_signed']}, Party B signed: {contract['party_b_signed']}")
else:
    print(f"❌ Failed to retrieve contracts: {r.json()}")

# Step 10: Both parties sign second contract
print(f"\n10. Both parties signing contract {contract2_id}...")
r1 = requests.post(f"{BASE_URL}/contracts/{contract2_id}/sign", json={"user_id": farmer_id})
r2 = requests.post(f"{BASE_URL}/contracts/{contract2_id}/sign", json={"user_id": worker_id})
if r1.status_code == 200 and r2.status_code == 200:
    data = r2.json()
    print(f"✅ Both parties signed contract {contract2_id}")
    print(f"   Status: {data['status']}")
else:
    print(f"❌ Failed to complete signing")

# Step 11: Test unauthorized signing
print(f"\n11. Testing unauthorized contract signing...")
r = requests.post(f"{BASE_URL}/contracts/{contract1_id}/sign", json={"user_id": worker_id})
if r.status_code == 403:
    print(f"✅ Correctly blocked unauthorized user: {r.json()['error']}")
else:
    print(f"❌ Security issue: Unauthorized user was able to sign!")

print("\n" + "=" * 70)
print("✅ All messaging & contract workflow tests completed successfully!")
print("=" * 70)
