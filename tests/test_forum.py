import pytest
from datetime import datetime, timezone

@pytest.fixture
def sample_user(client):
    response = client.post('/register', json={
        'full_name': 'Forum User',
        'email': 'forumuser@test.com',
        'password': 'password123',
        'account_type': 'farmer'
    })
    return response.get_json()

@pytest.fixture
def sample_admin(client):
    """Create a super admin and use it to create an admin"""
    # First create super admin directly in the database
    from models import User
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import config
        
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create super admin
        super_admin = User(
            full_name='Super Admin Forum',
            email='superadmin_forum@test.com',
            account_type='super_admin'
        )
        super_admin.set_password('admin123')
        session.add(super_admin)
        session.commit()
        super_admin_id = super_admin.id
        session.close()
    
    # Now create admin via API
    response = client.post('/admin/create-admin', json={
        'admin_id': super_admin_id,
        'full_name': 'Test Admin Forum',
        'email': 'admin_forum@test.com',
        'password': 'password123'
    })
    
    return response.get_json()

class TestForum:
    def test_create_post(self, client, sample_user):
        response = client.post('/forum/posts', json={
            'author_id': sample_user['id'],
            'title': 'Best time to plant maize?',
            'content': 'I am in Lagos, when should I plant?',
            'category': 'planting_advice',
            'location_state': 'Lagos',
            'crop_type': 'maize'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == 'Best time to plant maize?'
        assert data['upvotes'] == 0

    def test_get_posts(self, client, sample_user):
        # Create two posts
        client.post('/forum/posts', json={
            'author_id': sample_user['id'],
            'title': 'Post 1',
            'content': 'Content 1',
            'category': 'general'
        })
        client.post('/forum/posts', json={
            'author_id': sample_user['id'],
            'title': 'Post 2',
            'content': 'Content 2',
            'category': 'pest_control'
        })
        
        # Get all
        response = client.get('/forum/posts')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        
        # Filter by category
        response = client.get('/forum/posts?category=pest_control')
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['title'] == 'Post 2'

    def test_add_comment(self, client, sample_user):
        # Create post
        post = client.post('/forum/posts', json={
            'author_id': sample_user['id'],
            'title': 'Question',
            'content': 'Help',
            'category': 'general'
        }).get_json()
        
        # Add comment
        response = client.post(f'/forum/posts/{post["id"]}/comments', json={
            'author_id': sample_user['id'],
            'content': 'Here is help'
        })
        assert response.status_code == 201
        
        # Verify comment in post details
        response = client.get(f'/forum/posts/{post["id"]}')
        data = response.get_json()
        assert len(data['comments']) == 1
        assert data['comments'][0]['content'] == 'Here is help'

    def test_vote_post(self, client, sample_user):
        # Create post
        post = client.post('/forum/posts', json={
            'author_id': sample_user['id'],
            'title': 'Vote me',
            'content': 'Pls',
            'category': 'general'
        }).get_json()
        
        # Vote
        response = client.post(f'/forum/posts/{post["id"]}/vote', json={
            'user_id': sample_user['id'],
            'vote_type': 'upvote'
        })
        assert response.status_code == 200
        assert response.get_json()['upvotes'] == 1
        
        # Duplicate vote
        response = client.post(f'/forum/posts/{post["id"]}/vote', json={
            'user_id': sample_user['id'],
            'vote_type': 'upvote'
        })
        assert response.status_code == 409

    def test_banned_user_cannot_post(self, client, sample_admin):
        # Create user
        user = client.post('/register', json={
            'full_name': 'Bad User',
            'email': 'bad@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()
        
        # Ban user
        client.post(f'/admin/users/{user["id"]}/ban', json={
            'admin_id': sample_admin['id'],
            'reason': 'Spamming'
        })
        
        # Try to post
        response = client.post('/forum/posts', json={
            'author_id': user['id'],
            'title': 'Spam',
            'content': 'Spam',
            'category': 'general'
        })
        assert response.status_code == 403
        assert 'account is banned' in response.get_json()['error']
