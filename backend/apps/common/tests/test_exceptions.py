import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(db):
    client = APIClient()
    user = User.objects.create_user(
        email='exc@test.com',
        username='excuser',
        password='testpass123',
    )
    res = client.post('/api/auth/token/', {
        'email': 'exc@test.com', 'password': 'testpass123'
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')
    return client


@pytest.mark.django_db
class TestGlobalExceptionHandler:

    def test_404_returns_error_envelope(self, client):
        res = client.get('/api/comments/00000000-0000-0000-0000-000000000000/')
        assert res.status_code == 404
        assert 'error' in res.data
        assert res.data['error']['code'] == 'not_found'

    def test_401_returns_error_envelope(self, client):
        res = client.post('/api/comments/', {'content': 'test'}, format='json')
        assert res.status_code == 401
        assert res.data['error']['code'] == 'authentication_required'

    def test_400_validation_error_envelope(self, auth_client):
        res = auth_client.post('/api/comments/', {'content': ''}, format='json')
        assert res.status_code == 400
        assert 'error' in res.data

    def test_health_check_is_unaffected(self, client):
        res = client.get('/api/health/')
        assert res.status_code == 200
        assert 'status' in res.data


@pytest.mark.django_db
class TestPagination:

    def test_page_size_capped_at_100(self, auth_client):
        res = auth_client.get('/api/comments/?page_size=99999')
        assert res.status_code == 200
        assert res.data['pagination']['page_size'] <= 100

    def test_pagination_envelope_present(self, auth_client):
        res = auth_client.get('/api/comments/')
        assert 'pagination' in res.data
        assert 'results' in res.data
        assert 'count' in res.data['pagination']


@pytest.mark.django_db
class TestFiltering:

    def test_filter_by_author_id(self, auth_client):
        user = User.objects.get(email='exc@test.com')
        auth_client.post('/api/comments/', {'content': 'Filtered comment'}, format='json')
        res = auth_client.get(f'/api/comments/?author_id={user.id}')
        assert res.status_code == 200

    def test_invalid_sort_falls_back_to_latest(self, auth_client):
        res = auth_client.get('/api/comments/?sort=garbage')
        assert res.status_code == 200