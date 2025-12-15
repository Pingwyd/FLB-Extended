import sqlite3, json, os
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'flb.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# find an admin or super_admin id
cur.execute("SELECT id, full_name, account_type FROM users WHERE account_type IN ('admin','super_admin') LIMIT 1")
admin = cur.fetchone()
admin_id = admin['id'] if admin else None
print('Found admin:', dict(admin) if admin else None)

# fetch recent fee transactions
cur.execute("SELECT id, wallet_id, amount, transaction_type, status, reference, description, created_at FROM transactions WHERE transaction_type='fee' ORDER BY created_at DESC LIMIT 20")
fees = [dict(r) for r in cur.fetchall()]
print('\nRecent fee transactions (transaction_type=\'fee\') count=', len(fees))
print(json.dumps(fees, indent=2, default=str))

# also fetch recent withdrawals to cross-check
cur.execute("SELECT id, wallet_id, amount, transaction_type, status, reference, description, created_at FROM transactions WHERE transaction_type='withdrawal' ORDER BY created_at DESC LIMIT 20")
withdrawals = [dict(r) for r in cur.fetchall()]
print('\nRecent withdrawal transactions count=', len(withdrawals))
print(json.dumps(withdrawals, indent=2, default=str))

conn.close()
