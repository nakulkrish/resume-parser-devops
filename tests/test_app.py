import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'resume-parser'

def test_index(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Resume Parser' in resp.data