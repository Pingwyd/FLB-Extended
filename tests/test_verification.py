import json
import pytest


def test_upload_document(client):
    """Test document upload"""
    # First, register a user
    user_payload = {
        'full_name': 'Test User',
        'email': 'doctest@example.com',
        'password': 'pass123',
        'account_type': 'farmer'
    }
    rv = client.post('/register', data=json.dumps(user_payload), content_type='application/json')
    assert rv.status_code == 201
    user = rv.get_json()
    user_id = user['id']

    # Upload document
    doc_payload = {
        'user_id': user_id,
        'document_type': 'NIN',
        'document_number': '12345678901'
    }
    rv = client.post('/documents/upload', data=json.dumps(doc_payload), content_type='application/json')
    assert rv.status_code == 201
    doc = rv.get_json()
    assert doc['document_type'] == 'NIN'
    assert doc['status'] == 'pending'
    assert doc['user_id'] == user_id


def test_upload_document_invalid_type(client):
    """Test document upload with invalid document type"""
    # Register a user first
    user_payload = {
        'full_name': 'Test User2',
        'email': 'doctest2@example.com',
        'password': 'pass123',
        'account_type': 'worker'
    }
    rv = client.post('/register', data=json.dumps(user_payload), content_type='application/json')
    user_id = rv.get_json()['id']

    # Try invalid document type
    doc_payload = {
        'user_id': user_id,
        'document_type': 'invalid_doc',
        'document_number': '123'
    }
    rv = client.post('/documents/upload', data=json.dumps(doc_payload), content_type='application/json')
    assert rv.status_code == 400
    assert 'Invalid document_type' in rv.get_json()['error']


def test_get_user_documents(client):
    """Test retrieving user documents"""
    # Register user and upload document
    user_payload = {
        'full_name': 'Doc Retrieval User',
        'email': 'docret@example.com',
        'password': 'pass123',
        'account_type': 'farmer'
    }
    rv = client.post('/register', data=json.dumps(user_payload), content_type='application/json')
    user_id = rv.get_json()['id']

    # Upload two documents
    doc1 = {
        'user_id': user_id,
        'document_type': 'NIN',
        'document_number': '11111111111'
    }
    client.post('/documents/upload', data=json.dumps(doc1), content_type='application/json')

    doc2 = {
        'user_id': user_id,
        'document_type': 'passport',
        'document_number': 'A12345678'
    }
    client.post('/documents/upload', data=json.dumps(doc2), content_type='application/json')

    # Retrieve documents
    rv = client.get(f'/documents/{user_id}')
    assert rv.status_code == 200
    docs = rv.get_json()
    assert len(docs) == 2


def test_admin_approve_document(client):
    """Test admin approving a document"""
    # Create admin directly in database (since regular registration no longer allows admin type)
    from models import User
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import config
        
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create admin user
        admin = User(
            full_name='Admin User',
            email='admin@example.com',
            account_type='admin'
        )
        admin.set_password('adminpass')
        session.add(admin)
        session.commit()
        admin_id = admin.id
        session.close()

    # Register regular user
    user_payload = {
        'full_name': 'Regular User',
        'email': 'regular@example.com',
        'password': 'pass123',
        'account_type': 'farmer'
    }
    rv = client.post('/register', data=json.dumps(user_payload), content_type='application/json')
    user_id = rv.get_json()['id']

    # Upload document
    doc_payload = {
        'user_id': user_id,
        'document_type': 'NIN',
        'document_number': '99999999999'
    }
    rv = client.post('/documents/upload', data=json.dumps(doc_payload), content_type='application/json')
    doc_id = rv.get_json()['id']

    # Admin approves document
    verify_payload = {
        'status': 'approved',
        'admin_id': admin_id,
        'admin_notes': 'Document verified successfully'
    }
    rv = client.post(f'/documents/verify/{doc_id}', data=json.dumps(verify_payload), content_type='application/json')
    assert rv.status_code == 200
    doc = rv.get_json()
    assert doc['status'] == 'approved'
    assert doc['admin_notes'] == 'Document verified successfully'
    assert doc['reviewed_by'] == admin_id


def test_non_admin_cannot_verify(client):
    """Test that non-admin users cannot verify documents"""
    # Register regular user (not admin)
    user_payload = {
        'full_name': 'Non Admin',
        'email': 'nonadmin@example.com',
        'password': 'pass123',
        'account_type': 'worker'
    }
    rv = client.post('/register', data=json.dumps(user_payload), content_type='application/json')
    user_id = rv.get_json()['id']

    # Upload document
    doc_payload = {
        'user_id': user_id,
        'document_type': 'NIN',
        'document_number': '88888888888'
    }
    rv = client.post('/documents/upload', data=json.dumps(doc_payload), content_type='application/json')
    doc_id = rv.get_json()['id']

    # Try to verify with non-admin user
    verify_payload = {
        'status': 'approved',
        'admin_id': user_id
    }
    rv = client.post(f'/documents/verify/{doc_id}', data=json.dumps(verify_payload), content_type='application/json')
    assert rv.status_code == 403
    assert 'unauthorized' in rv.get_json()['error']
