import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'flb.db')

print('DB path:', DB_PATH)
if not os.path.exists(DB_PATH):
    print('Database file not found at', DB_PATH)
    exit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check if table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_audit_logs';")
if not cur.fetchone():
    print('Table admin_audit_logs not found. Nothing to do.')
    conn.close()
    exit(0)

# Check if column 'read' exists
cur.execute("PRAGMA table_info('admin_audit_logs');")
cols = [r[1] for r in cur.fetchall()]
print('Existing columns:', cols)
if 'read' in cols:
    print("Column 'read' already exists. No action needed.")
    conn.close()
    exit(0)

# Add the column
try:
    print("Adding column 'read' to admin_audit_logs...")
    cur.execute("ALTER TABLE admin_audit_logs ADD COLUMN read BOOLEAN DEFAULT 0;")
    conn.commit()
    print("Column added.")
except Exception as e:
    print('Error adding column:', e)
    conn.rollback()
    conn.close()
    exit(1)

# Show updated columns
cur.execute("PRAGMA table_info('admin_audit_logs');")
cols = [r[1] for r in cur.fetchall()]
print('Updated columns:', cols)

conn.close()
print('Migration completed successfully.')
