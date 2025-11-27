import pytest
import os
import tempfile
from app import create_app

@pytest.fixture
def app():
    # Create a temporary database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Temporarily override the database URI
    import config
    old_uri = config.SQLALCHEMY_DATABASE_URI
    config.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    app = create_app()
    app.testing = True
    
    yield app
    
    # Cleanup
    config.SQLALCHEMY_DATABASE_URI = old_uri
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()
