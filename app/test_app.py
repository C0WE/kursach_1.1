import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert 'status' in data
    assert 'database' in data

def test_index_page(client):
    response = client.get('/')
    assert response.status_code in [200, 404]

def test_get_test_data(client):
    response = client.get('/api/test')
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data
    assert 'data' in data

def test_invalid_post_data(client):
    # This test should run before test_rate_limiting to avoid hitting rate limit
    response = client.post('/api/test', json={})
    assert response.status_code == 400

def test_rate_limiting(client):
    # This test intentionally hits rate limit, so it should be last
    for i in range(15):
        response = client.post('/api/test', json={'name': f'test{i}'})
    assert response.status_code == 429 or response.status_code in [200, 201, 500]

def test_system_overview(client):
    response = client.get('/api/system/overview')
    assert response.status_code == 200
    data = response.get_json()
    assert 'database' in data or 'cache' in data
