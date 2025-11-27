from app import create_app
from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def create_super_admin():
    # Setup DB connection
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    email = "superadmin@flb.com"
    password = "SuperAdminPass123!"
    
    # Check if user exists
    existing_user = session.query(User).filter_by(email=email).first()
    
    if existing_user:
        print(f"User {email} already exists.")
        existing_user.set_password(password)
        existing_user.account_type = 'super_admin'
        existing_user.verified = True
        existing_user.email_verified = True
        session.commit()
        print(f"Updated {email} to super_admin with new password.")
    else:
        new_user = User(
            full_name="Super Admin",
            email=email,
            account_type="super_admin",
            verified=True,
            email_verified=True
        )
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        print(f"Created new super_admin: {email}")
        
    session.close()

if __name__ == "__main__":
    create_super_admin()
