import sqlite3
import os

# Database file path
DB_FILE = 'flb.db'

def migrate_db():
    if not os.path.exists(DB_FILE):
        print(f"Error: Database file '{DB_FILE}' not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Add party_a_signature column
        try:
            print("Adding column 'party_a_signature' to 'contracts' table...")
            cursor.execute("ALTER TABLE contracts ADD COLUMN party_a_signature TEXT")
            print("Column 'party_a_signature' added.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'party_a_signature' already exists.")
            else:
                print(f"Error adding 'party_a_signature': {e}")

        # Add party_b_signature column
        try:
            print("Adding column 'party_b_signature' to 'contracts' table...")
            cursor.execute("ALTER TABLE contracts ADD COLUMN party_b_signature TEXT")
            print("Column 'party_b_signature' added.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'party_b_signature' already exists.")
            else:
                print(f"Error adding 'party_b_signature': {e}")

        conn.commit()
        print("Migration complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
