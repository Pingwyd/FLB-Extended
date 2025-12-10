from app import create_app
from models import ForumPost, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

app = create_app()
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

try:
    posts = session.query(ForumPost).all()
    print(f"Total posts: {len(posts)}")
    for post in posts:
        print(f"Post ID: {post.id}, Title: {post.title}, Category: {post.category}")
except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
