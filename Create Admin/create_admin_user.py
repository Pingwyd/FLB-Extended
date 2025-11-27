from app import create_app
from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def create_admin():
    # Create app to ensure context (though we might just need the DB connection)
    app = create_app()
    
    # Setup DB connection
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fix schema if needed (Add missing columns)
    from sqlalchemy import text
    try:
        # Check if email_verified exists
        try:
            session.execute(text("SELECT email_verified FROM users LIMIT 1"))
        except Exception:
            print("Adding missing column: email_verified")
            session.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
        
        # Check if is_banned exists
        try:
            session.execute(text("SELECT is_banned FROM users LIMIT 1"))
        except Exception:
            print("Adding missing column: is_banned")
            session.execute(text("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0"))
            session.execute(text("ALTER TABLE users ADD COLUMN banned_at DATETIME"))
            session.execute(text("ALTER TABLE users ADD COLUMN banned_by INTEGER REFERENCES users(id)"))
            session.execute(text("ALTER TABLE users ADD COLUMN ban_reason TEXT"))

        # Check if average_rating exists
        try:
            session.execute(text("SELECT average_rating FROM users LIMIT 1"))
        except Exception:
            print("Adding missing column: average_rating")
            session.execute(text("ALTER TABLE users ADD COLUMN average_rating FLOAT DEFAULT 0.0"))
            session.execute(text("ALTER TABLE users ADD COLUMN rating_count INTEGER DEFAULT 0"))

        # Check if otp_code exists
        try:
            session.execute(text("SELECT otp_code FROM users LIMIT 1"))
        except Exception:
            print("Adding missing column: otp_code")
            session.execute(text("ALTER TABLE users ADD COLUMN otp_code VARCHAR(6)"))
            session.execute(text("ALTER TABLE users ADD COLUMN otp_expiry DATETIME"))
        
        session.commit()
    except Exception as e:
        print(f"Schema update warning: {e}")
        session.rollback()
    
    email = "admin@flb.com"
    password = "AdminPass123!"
    
    # Check if admin exists
    existing_admin = session.query(User).filter_by(email=email).first()
    
    if existing_admin:
        print(f"Admin user {email} already exists.")
        # Update password just in case
        existing_admin.set_password(password)
        existing_admin.account_type = 'super_admin' # Ensure they have full privileges
        session.commit()
        print(f"Updated password for {email}")
    else:
        new_admin = User(
            full_name="System Admin",
            email=email,
            account_type="super_admin",
            verified=True,
            email_verified=True
        )
        new_admin.set_password(password)
        session.add(new_admin)
        session.commit()
        print(f"Created new admin user: {email}")
        
    session.close()

if __name__ == "__main__":
    create_admin()
