import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

class TestWithdrawalManual(unittest.TestCase):
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
            # We need to ensure tables are created
            # create_app does this automatically with the memory DB
            pass

    def tearDown(self):
        import config
        config.SQLALCHEMY_DATABASE_URI = self.original_db_uri

    def test_withdrawal_flow(self):
        # 1. Create User
        user_res = self.client.post('/register', json={
            'full_name': 'Withdrawal User',
            'email': 'withdraw@example.com',
            'password': 'password123',
            'account_type': 'worker'
        })
        user_id = user_res.json['id']

        # 2. Fund Wallet (Simulate deposit)
        # We can't easily inject into DB without session access, so we use the fund endpoint
        # But fund endpoint creates a 'pending' transaction.
        # We need a way to force a balance update for testing.
        # Or we can use the callback endpoint to "complete" a fake transaction.
        
        # Step 2a: Initialize funding
        fund_res = self.client.post('/api/wallet/fund', json={
            'user_id': user_id,
            'amount': 10000,
            'email': 'withdraw@example.com'
        })
        txn_ref = fund_res.json['txn_ref']
        
        # Step 2b: Mock Interswitch verification to succeed
        with patch('app.requests.get') as mock_get:
            # We need to mock the response to match the expected amount (amount + fee)
            # Fee is 1.5% of 10000 = 150. Total = 10150.
            # Amount in kobo = 1015000
            mock_get.return_value.json.return_value = {
                'ResponseCode': '00',
                'Amount': '1015000' 
            }
            
            # Call callback to credit wallet
            self.client.get(f'/api/payment/callback?txn_ref={txn_ref}')

        # Verify balance
        bal_res = self.client.get(f'/api/wallet/balance/{user_id}')
        self.assertEqual(bal_res.json['balance'], 10000.0)

        # 3. Add Bank Account
        bank_res = self.client.post('/api/bank-accounts', json={
            'user_id': user_id,
            'bank_name': 'Test Bank',
            'account_number': '1234567890',
            'account_name': 'Withdrawal User'
        })
        self.assertEqual(bank_res.status_code, 201)
        bank_id = bank_res.json['id']

        # 4. Request Withdrawal
        # Balance is 10000. Withdrawal is 5000. Fee is 100. Total deduction 5100.
        withdraw_res = self.client.post('/api/wallet/withdraw', json={
            'user_id': user_id,
            'amount': 5000,
            'bank_account_id': bank_id
        })
        self.assertEqual(withdraw_res.status_code, 201)
        self.assertEqual(withdraw_res.json['new_balance'], 4900.0) # 10000 - 5000 - 100
        self.assertEqual(withdraw_res.json['transaction']['status'], 'pending')
        self.assertEqual(withdraw_res.json['transaction']['transaction_type'], 'withdrawal')
        self.assertEqual(withdraw_res.json['fee_amount'], 100.0)

        # 5. Verify Final Balance
        bal_res_final = self.client.get(f'/api/wallet/balance/{user_id}')
        self.assertEqual(bal_res_final.json['balance'], 4900.0)

    def test_insufficient_funds(self):
        # 1. Create User
        user_res = self.client.post('/register', json={
            'full_name': 'Poor User',
            'email': 'poor@example.com',
            'password': 'password123',
            'account_type': 'worker'
        })
        user_id = user_res.json['id']

        # 2. Add Bank Account
        bank_res = self.client.post('/api/bank-accounts', json={
            'user_id': user_id,
            'bank_name': 'Test Bank',
            'account_number': '0000000000',
            'account_name': 'Poor User'
        })
        bank_id = bank_res.json['id']

        # 3. Try to withdraw (Balance is 0)
        withdraw_res = self.client.post('/api/wallet/withdraw', json={
            'user_id': user_id,
            'amount': 100,
            'bank_account_id': bank_id
        })
        self.assertEqual(withdraw_res.status_code, 400)
        self.assertIn('Insufficient funds', withdraw_res.json['error'])

if __name__ == '__main__':
    unittest.main()
