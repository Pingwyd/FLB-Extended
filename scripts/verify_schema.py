import sqlite3
import os

DB_PATH = 'flb.db'

def verify_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables_to_check = {
        'worker_profiles': ['is_boosted', 'boost_expiry'],
        'listings': ['boost_expiry'],
        'forum_comments': ['parent_id']
    }

    for table, required_columns in tables_to_check.items():
        print(f"Checking table '{table}'...")
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [info[1] for info in cursor.fetchall()]
        
        for col in required_columns:
            if col in existing_columns:
                print(f"  [OK] Column '{col}' exists.")
            else:
                print(f"  [MISSING] Column '{col}' is MISSING!")

    conn.close()

if __name__ == "__main__":
    verify_schema()
