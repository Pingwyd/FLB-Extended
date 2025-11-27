import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import Wallet, Transaction, User

class TestPaymentManual(unittest.TestCase):
    def setUp(self):
        # Configure test database
        import config
        self.original_db_uri = config.SQLALCHEMY_DATABASE_URI
        config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Setup database
        with self.app.app_context():
            from models import Base
            # We need to use the engine from the app, but it's not exposed directly
            # However, since we set the config to memory, create_app created an engine with memory DB
            # But we can't easily access that engine to create tables if create_app didn't do it.
            # create_app does: Base.metadata.create_all(bind=engine)
            pass

    def tearDown(self):
        import config
        config.SQLALCHEMY_DATABASE_URI = self.original_db_uri

    def test_fund_wallet_init(self):
        # Test that fund wallet returns the correct Interswitch form parameters
        data = {
            'user_id': 1,
            'amount': 5000,
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        response = self.client.post('/api/wallet/fund', json=data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.json)
        self.assertIn('merchant_code', response.json)
        self.assertIn('txn_ref', response.json)
        # 5000 + 1.5% fee (75) = 5075. 5075 * 100 = 507500 kobo
        self.assertEqual(response.json['amount'], 507500) 

    @patch('app.requests.get')
    def test_payment_callback(self, mock_get):
        # Mock Interswitch verification response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ResponseCode': '00',
            'ResponseDescription': 'Approved',
            'Amount': '507500', # 5075 * 100 (includes fee)
            'CardNumber': '123456******1234',
            'MerchantReference': 'ref_12345',
            'PaymentDate': '2023-01-01T12:00:00',
            'RetrievalReferenceNumber': '123456789012'
        }
        mock_get.return_value = mock_response

        # First, create a pending transaction
        # We'll use the fund endpoint to create it and capture the ref
        
        fund_response = self.client.post('/api/wallet/fund', json={
            'user_id': 1,
            'amount': 5000,
            'email': 'test@example.com'
        })
        txn_ref = fund_response.json['txn_ref']

        # Now call callback with the captured ref
        response = self.client.get(f'/api/payment/callback?txn_ref={txn_ref}')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        self.assertEqual(response.json['amount'], 5000.0)
        
        # Check balance
        balance_response = self.client.get('/api/wallet/balance/1')
        self.assertEqual(balance_response.json['balance'], 5000.0)

    @patch('app.requests.get')
    def test_payment_callback_failed(self, mock_get):
        # Mock Interswitch verification response for failure
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'ResponseCode': 'Z0',
            'ResponseDescription': 'Insufficient Funds',
            'Amount': '507500'
        }
        mock_get.return_value = mock_response

        # Create transaction
        fund_response = self.client.post('/api/wallet/fund', json={
            'user_id': 2,
            'amount': 5000,
            'email': 'test2@example.com'
        })
        txn_ref = fund_response.json['txn_ref']

        # Call callback
        response = self.client.get(f'/api/payment/callback?txn_ref={txn_ref}')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('failed', response.json['error'])

if __name__ == '__main__':
    unittest.main()
