import json
import pytest
from models import AdminAuditLog, User
import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_audit_logging_verification(client, app):
    # 1. Register User
    user_payload = {
        'full_name': 'Audit User',
        'email': 'audit@example.com',
        'password': 'StrongPass1',
        'account_type': 'farmer'
    }
    rv = client.post('/register', data=json.dumps(user_payload), content_type='application/json')
    assert rv.status_code == 201
    user_id = rv.get_json()['id']

    # 2. Upload Document
    doc_payload = {
        'user_id': user_id,
        'document_type': 'NIN',
        'document_number': '12345678901'
    }
    rv = client.post('/documents/upload', data=json.dumps(doc_payload), content_type='application/json')
    assert rv.status_code == 201
    doc_id = rv.get_json()['id']

    # 3. Create Admin
    # We need to do this via DB session as /register doesn't allow admin
    with app.app_context():
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if admin exists
        existing = session.query(User).filter_by(email='admin_audit@example.com').first()
        if existing:
            session.delete(existing)
            session.commit()

        admin = User(full_name='Admin Audit', email='admin_audit@example.com', account_type='admin')
        admin.set_password('StrongPass1')
        session.add(admin)
        session.commit()
        session.refresh(admin)
        admin_id = admin.id
        session.close()

    # 4. Admin Views Document
    rv = client.get(f'/documents/{user_id}?admin_id={admin_id}')
    assert rv.status_code == 200

    # Check Audit Log for View
    with app.app_context():
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        log = session.query(AdminAuditLog).filter_by(
            admin_id=admin_id, 
            action='view_verification_docs',
            target_id=user_id
        ).first()
        
        assert log is not None
        assert log.target_type == 'user'
        session.close()

    # 5. Admin Verifies Document
    verify_payload = {
        'status': 'approved',
        'admin_id': admin_id,
        'admin_notes': 'Looks good'
    }
    rv = client.post(f'/documents/verify/{doc_id}', data=json.dumps(verify_payload), content_type='application/json')
    assert rv.status_code == 200

    # Check Audit Log for Verify
    with app.app_context():
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        log = session.query(AdminAuditLog).filter_by(
            admin_id=admin_id, 
            action='verify_document_approved',
            target_id=doc_id
        ).first()
        
        assert log is not None
        assert log.target_type == 'verification_document'
        assert log.reason == 'Looks good'
        session.close()
