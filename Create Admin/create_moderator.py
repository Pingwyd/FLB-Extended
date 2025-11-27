from app import create_app
from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def create_moderator():
    # Setup DB connection
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    email = "moderator@flb.com"
    password = "ModeratorPass123!"
    
    # Check if user exists
    existing_user = session.query(User).filter_by(email=email).first()
    
    if existing_user:
        print(f"User {email} already exists.")
        existing_user.set_password(password)
        existing_user.account_type = 'moderator'
        existing_user.verified = True
        existing_user.email_verified = True
        session.commit()
        print(f"Updated {email} to moderator with new password.")
    else:
        new_user = User(
            full_name="System Moderator",
            email=email,
            account_type="moderator",
            verified=True,
            email_verified=True
        )
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        print(f"Created new moderator: {email}")
        
    session.close()

if __name__ == "__main__":
    create_moderator()
