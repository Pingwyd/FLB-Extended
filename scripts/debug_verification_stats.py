
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Base, User, VerificationDocument
from config import SQLALCHEMY_DATABASE_URI

# Setup database connection
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # 1. Total users
    total_users = session.query(User).count()
    print(f"Total Users: {total_users}")

    # 2. Verified users
    verified_users = session.query(User).filter(User.verified == True).count()
    print(f"Verified Users: {verified_users}")

    # 3. Unverified users
    unverified_users = session.query(User).filter(User.verified == False).count()
    print(f"Unverified Users: {unverified_users}")

    # 4. Total Verification Documents
    total_docs = session.query(VerificationDocument).count()
    print(f"Total Verification Documents: {total_docs}")

    # 5. Documents by status
    docs_by_status = session.query(VerificationDocument.status, func.count(VerificationDocument.status)).group_by(VerificationDocument.status).all()
    print("Documents by Status:")
    for status, count in docs_by_status:
        print(f"  - {status}: {count}")

    # 6. Users with pending documents
    users_with_pending_docs = session.query(User).join(VerificationDocument).filter(VerificationDocument.status == 'pending').count()
    print(f"Users with Pending Documents: {users_with_pending_docs}")

    # 7. Check for orphaned documents (user_id not in users) - unlikely with FK but good to check
    # orphaned_docs = session.query(VerificationDocument).filter(~VerificationDocument.user_id.in_(session.query(User.id))).count()
    # print(f"Orphaned Documents: {orphaned_docs}")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
