import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from apps.comments.models import Comment
from apps.comments.services import CommentService

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='svc@example.com',
        username='svcuser',
        password='testpass123',
    )

@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email='other@example.com',
        username='otheruser',
        password='testpass123',
    )


@pytest.mark.django_db
class TestCommentService:

    def test_create_comment(self, user):
        comment = CommentService.create_comment(author=user, content='Hello')
        assert comment.content == 'Hello'
        assert comment.author == user

    def test_create_comment_strips_whitespace(self, user):
        comment = CommentService.create_comment(author=user, content='  Hello  ')
        assert comment.content == 'Hello'

    def test_create_comment_empty_raises(self, user):
        with pytest.raises(ValidationError):
            CommentService.create_comment(author=user, content='   ')

    def test_create_reply_increments_parent_reply_count(self, user):
        parent = CommentService.create_comment(author=user, content='Parent')
        CommentService.create_reply(author=user, parent_id=parent.id, content='Reply')
        parent.refresh_from_db()
        assert parent.reply_count == 1

    def test_create_reply_to_deleted_parent_raises(self, user):
        parent = CommentService.create_comment(author=user, content='Parent')
        CommentService.delete_comment(comment_id=parent.id, requesting_user=user)
        with pytest.raises(ValidationError):
            CommentService.create_reply(
                author=user, parent_id=parent.id, content='Reply'
            )

    def test_edit_comment(self, user):
        comment = CommentService.create_comment(author=user, content='Original')
        updated = CommentService.edit_comment(
            comment_id=comment.id,
            requesting_user=user,
            content='Updated',
        )
        assert updated.content == 'Updated'

    def test_edit_comment_wrong_user_raises(self, user, other_user):
        comment = CommentService.create_comment(author=user, content='Original')
        with pytest.raises(PermissionDenied):
            CommentService.edit_comment(
                comment_id=comment.id,
                requesting_user=other_user,
                content='Hijacked',
            )

    def test_delete_comment_soft_deletes(self, user):
        comment = CommentService.create_comment(author=user, content='Delete me')
        CommentService.delete_comment(comment_id=comment.id, requesting_user=user)
        comment.refresh_from_db()
        assert comment.is_deleted is True
        assert comment.content == '[deleted]'

    def test_delete_comment_decrements_parent_reply_count(self, user):
        parent = CommentService.create_comment(author=user, content='Parent')
        reply = CommentService.create_reply(
            author=user, parent_id=parent.id, content='Reply'
        )
        parent.refresh_from_db()
        assert parent.reply_count == 1

        CommentService.delete_comment(comment_id=reply.id, requesting_user=user)
        parent.refresh_from_db()
        assert parent.reply_count == 0

    def test_delete_wrong_user_raises(self, user, other_user):
        comment = CommentService.create_comment(author=user, content='Mine')
        with pytest.raises(PermissionDenied):
            CommentService.delete_comment(
                comment_id=comment.id, requesting_user=other_user
            )