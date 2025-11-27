import sqlite3
import os

# Path to the database file
DB_PATH = 'flb.db'

def fix_db_schema_all():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Fix listings table
        print("Checking 'listings' table...")
        cursor.execute("PRAGMA table_info(listings)")
        columns_listings = [info[1] for info in cursor.fetchall()]
        
        if 'boost_expiry' not in columns_listings:
            print("Adding 'boost_expiry' column to listings table...")
            cursor.execute("ALTER TABLE listings ADD COLUMN boost_expiry DATETIME")
        else:
            print("'boost_expiry' column already exists in listings.")

        # 2. Fix forum_comments table
        print("Checking 'forum_comments' table...")
        cursor.execute("PRAGMA table_info(forum_comments)")
        columns_comments = [info[1] for info in cursor.fetchall()]
        
        if 'parent_id' not in columns_comments:
            print("Adding 'parent_id' column to forum_comments table...")
            cursor.execute("ALTER TABLE forum_comments ADD COLUMN parent_id INTEGER REFERENCES forum_comments(id)")
        else:
            print("'parent_id' column already exists in forum_comments.")

        conn.commit()
        print("All schema updates completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_db_schema_all()
