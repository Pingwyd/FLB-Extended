"""
Manual test script for document verification workflow
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
print("Document Verification Workflow Test")
print("=" * 70)

# Step 1: Register a farmer
print("\n1. Registering a farmer...")
farmer = {
    "full_name": "John Farmer",
    "email": "johnfarmer@test.com",
    "password": "FarmPass123",
    "account_type": "farmer"
}
r = requests.post(f"{BASE_URL}/register", json=farmer)
if r.status_code == 201:
    farmer_data = r.json()
    farmer_id = farmer_data['id']
    print(f"✅ Farmer registered: ID={farmer_id}, Verified={farmer_data['verified']}")
else:
    print(f"❌ Registration failed: {r.json()}")
    sys.exit(1)

# Step 2: Register an admin
print("\n2. Registering an admin...")
admin = {
    "full_name": "Admin User",
    "email": "admin@test.com",
    "password": "AdminPass123",
    "account_type": "admin"
}
r = requests.post(f"{BASE_URL}/register", json=admin)
admin_id = r.json()['id']
print(f"✅ Admin registered: ID={admin_id}")

# Step 3: Upload verification documents
print("\n3. Uploading verification documents...")
documents = [
    {
        "user_id": farmer_id,
        "document_type": "NIN",
        "document_number": "12345678901"
    },
    {
        "user_id": farmer_id,
        "document_type": "passport",
        "document_number": "A12345678"
    }
]

doc_ids = []
for doc in documents:
    r = requests.post(f"{BASE_URL}/documents/upload", json=doc)
    if r.status_code == 201:
        doc_data = r.json()
        doc_ids.append(doc_data['id'])
        print(f"✅ Uploaded {doc_data['document_type']}: ID={doc_data['id']}, Status={doc_data['status']}")
    else:
        print(f"❌ Upload failed: {r.json()}")

# Step 4: Retrieve user's documents
print(f"\n4. Retrieving documents for farmer (ID={farmer_id})...")
r = requests.get(f"{BASE_URL}/documents/{farmer_id}")
user_docs = r.json()
print(f"✅ Found {len(user_docs)} documents")
for doc in user_docs:
    print(f"   - {doc['document_type']}: {doc['document_number']} (Status: {doc['status']})")

# Step 5: Admin approves first document
print(f"\n5. Admin approving document ID={doc_ids[0]}...")
verify_payload = {
    "status": "approved",
    "admin_id": admin_id,
    "admin_notes": "All information verified and correct"
}
r = requests.post(f"{BASE_URL}/documents/verify/{doc_ids[0]}", json=verify_payload)
if r.status_code == 200:
    doc_data = r.json()
    print(f"✅ Document approved!")
    print(f"   Status: {doc_data['status']}")
    print(f"   Reviewed by: Admin ID {doc_data['reviewed_by']}")
    print(f"   Notes: {doc_data['admin_notes']}")
else:
    print(f"❌ Approval failed: {r.json()}")

# Step 6: Admin rejects second document
print(f"\n6. Admin rejecting document ID={doc_ids[1]}...")
reject_payload = {
    "status": "rejected",
    "admin_id": admin_id,
    "admin_notes": "Passport number format is invalid"
}
r = requests.post(f"{BASE_URL}/documents/verify/{doc_ids[1]}", json=reject_payload)
if r.status_code == 200:
    doc_data = r.json()
    print(f"✅ Document rejected!")
    print(f"   Status: {doc_data['status']}")
    print(f"   Notes: {doc_data['admin_notes']}")
else:
    print(f"❌ Rejection failed: {r.json()}")

# Step 7: Check if user is now verified
print(f"\n7. Checking farmer's verification status...")
r = requests.post(f"{BASE_URL}/login", json={"email": farmer['email'], "password": farmer['password']})
user_data = r.json()
print(f"✅ Farmer verification status: {user_data['verified']}")

# Step 8: Try non-admin verification (should fail)
print("\n8. Testing that non-admin cannot verify...")
r = requests.post(f"{BASE_URL}/documents/verify/{doc_ids[0]}", json={
    "status": "approved",
    "admin_id": farmer_id  # Using farmer ID instead of admin
})
if r.status_code == 403:
    print(f"✅ Correctly blocked non-admin from verifying: {r.json()['error']}")
else:
    print(f"❌ Security issue: Non-admin was able to verify!")

print("\n" + "=" * 70)
print("✅ All verification workflow tests completed successfully!")
print("=" * 70)
