import pytest
import werkzeug

# Some werkzeug/Flask distributions may not expose __version__ (packaging differences).
# Ensure it's present so Flask's test client can build a user-agent string.
if not hasattr(werkzeug, '__version__'):
    setattr(werkzeug, '__version__', '0')

from app import create_app

def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'ok'


def test_users_empty(client):
    rv = client.get('/users')
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
