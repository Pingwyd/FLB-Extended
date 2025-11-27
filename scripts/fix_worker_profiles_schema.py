import sqlite3
import os

# Path to the database file
DB_PATH = 'flb.db'

def fix_worker_profiles_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(worker_profiles)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_boosted' not in columns:
            print("Adding 'is_boosted' column to worker_profiles table...")
            cursor.execute("ALTER TABLE worker_profiles ADD COLUMN is_boosted BOOLEAN DEFAULT 0")
        else:
            print("'is_boosted' column already exists.")

        if 'boost_expiry' not in columns:
            print("Adding 'boost_expiry' column to worker_profiles table...")
            cursor.execute("ALTER TABLE worker_profiles ADD COLUMN boost_expiry DATETIME")
        else:
            print("'boost_expiry' column already exists.")

        conn.commit()
        print("Schema update completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_worker_profiles_schema()
