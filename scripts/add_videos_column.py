import sqlite3
import os

DB_PATH = 'flb.db'

def add_videos_column():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(listings)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'videos' in columns:
            print("Column 'videos' already exists in 'listings' table.")
        else:
            print("Adding 'videos' column to 'listings' table...")
            cursor.execute("ALTER TABLE listings ADD COLUMN videos TEXT")
            conn.commit()
            print("Column 'videos' added successfully.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_videos_column()
