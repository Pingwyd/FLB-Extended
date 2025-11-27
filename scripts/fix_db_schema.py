import sqlite3
import os

def migrate_database():
    db_path = 'flb.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Checking 'users' table schema...")
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # Columns to add to users table
    new_columns = {
        'profile_picture': 'VARCHAR(500)',
        'phone_number': 'VARCHAR(20)',
        'bio': 'TEXT',
        'location': 'VARCHAR(200)',
        'verified': 'BOOLEAN DEFAULT 0',
        'email_verified': 'BOOLEAN DEFAULT 0',
        'otp_code': 'VARCHAR(6)',
        'otp_expiry': 'DATETIME'
    }
    
    for col, dtype in new_columns.items():
        if col not in columns:
            print(f"Adding column '{col}' to 'users' table...")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
            except sqlite3.OperationalError as e:
                print(f"Error adding {col}: {e}")
        else:
            print(f"Column '{col}' already exists.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_database()
