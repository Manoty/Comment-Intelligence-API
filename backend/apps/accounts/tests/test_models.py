import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='securepassword123',
        )
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.check_password('securepassword123')

    def test_user_uuid_primary_key(self):
        user = User.objects.create_user(
            email='uuid@example.com',
            username='uuiduser',
            password='securepassword123',
        )
        assert user.pk is not None
        assert len(str(user.pk)) == 36  # UUID format

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == 'email'

    def test_reputation_score_defaults_to_zero(self):
        user = User.objects.create_user(
            email='rep@example.com',
            username='repuser',
            password='securepassword123',
        )
        assert user.reputation_score == 0.0

    def test_duplicate_email_raises_error(self):
        User.objects.create_user(
            email='dupe@example.com',
            username='user1',
            password='securepassword123',
        )
        with pytest.raises(Exception):
            User.objects.create_user(
                email='dupe@example.com',
                username='user2',
                password='securepassword123',
            )