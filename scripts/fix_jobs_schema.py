import sqlite3
import os

DB_PATH = 'flb.db'

def fix_jobs_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_boosted' not in columns:
            print("Adding is_boosted column to jobs table...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN is_boosted BOOLEAN DEFAULT 0")
            
        if 'boost_expiry' not in columns:
            print("Adding boost_expiry column to jobs table...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN boost_expiry DATETIME")
            
        conn.commit()
        print("Jobs schema updated successfully.")
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_jobs_schema()
