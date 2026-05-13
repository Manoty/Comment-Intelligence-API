import pytest
from django.contrib.auth import get_user_model
from apps.comments.models import Comment

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='commenter@example.com',
        username='commenter',
        password='testpass123',
    )


@pytest.mark.django_db
class TestCommentModel:

    def test_create_root_comment(self, user):
        comment = Comment.objects.create(author=user, content='Hello world')
        assert comment.id is not None
        assert comment.is_root is True
        assert comment.is_reply is False
        assert comment.is_deleted is False

    def test_create_reply(self, user):
        parent = Comment.objects.create(author=user, content='Parent comment')
        reply = Comment.objects.create(
            author=user, parent=parent, content='Reply comment'
        )
        assert reply.is_reply is True
        assert reply.parent_id == parent.id

    def test_default_score_and_counts(self, user):
        comment = Comment.objects.create(author=user, content='Test')
        assert comment.score == 0.0
        assert comment.like_count == 0
        assert comment.reply_count == 0

    def test_comment_uuid_primary_key(self, user):
        comment = Comment.objects.create(author=user, content='UUID test')
        assert len(str(comment.id)) == 36

    def test_soft_delete_keeps_record(self, user):
        comment = Comment.objects.create(author=user, content='Will be deleted')
        comment.is_deleted = True
        comment.content = '[deleted]'
        comment.save()
        assert Comment.objects.filter(id=comment.id).exists()