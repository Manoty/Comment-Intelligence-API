import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.comments.models import Comment

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='api@example.com',
        username='apiuser',
        password='testpass123',
    )


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post('/api/auth/token/', {
        'email': 'api@example.com',
        'password': 'testpass123',
    }, format='json')
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.mark.django_db
class TestCommentAPI:

    def test_create_comment(self, auth_client):
        response = auth_client.post('/api/comments/', {'content': 'Test comment'}, format='json')
        assert response.status_code == 201
        assert response.data['content'] == 'Test comment'

    def test_list_comments(self, auth_client, user):
        Comment.objects.create(author=user, content='First')
        Comment.objects.create(author=user, content='Second')
        response = auth_client.get('/api/comments/')
        assert response.status_code == 200
        assert len(response.data['results']) == 2

    def test_list_comments_unauthenticated(self, api_client, user):
        Comment.objects.create(author=user, content='Public')
        response = api_client.get('/api/comments/')
        assert response.status_code == 200

    def test_get_comment_detail(self, auth_client, user):
        comment = Comment.objects.create(author=user, content='Detail test')
        response = auth_client.get(f'/api/comments/{comment.id}/')
        assert response.status_code == 200
        assert response.data['content'] == 'Detail test'

    def test_edit_comment(self, auth_client, user):
        comment = Comment.objects.create(author=user, content='Old content')
        response = auth_client.patch(
            f'/api/comments/{comment.id}/',
            {'content': 'New content'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['content'] == 'New content'

    def test_delete_comment(self, auth_client, user):
        comment = Comment.objects.create(author=user, content='Delete me')
        response = auth_client.delete(f'/api/comments/{comment.id}/')
        assert response.status_code == 204

    def test_reply_to_comment(self, auth_client, user):
        parent = Comment.objects.create(author=user, content='Parent')
        response = auth_client.post(
            f'/api/comments/{parent.id}/reply/',
            {'content': 'This is a reply'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['content'] == 'This is a reply'

    def test_sort_by_latest(self, auth_client, user):
        Comment.objects.create(author=user, content='First')
        Comment.objects.create(author=user, content='Second')
        response = auth_client.get('/api/comments/?sort=latest')
        assert response.status_code == 200

    def test_create_comment_unauthenticated_fails(self, api_client):
        response = api_client.post('/api/comments/', {'content': 'Anon'}, format='json')
        assert response.status_code == 401