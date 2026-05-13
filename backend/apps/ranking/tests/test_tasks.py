import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestRankingTasks:

    def test_recalculate_score_task(self):
        from django.contrib.auth import get_user_model
        from apps.comments.models import Comment
        from apps.ranking.tasks import recalculate_score_for_comment

        User = get_user_model()
        user = User.objects.create_user(
            email='task@test.com',
            username='taskuser',
            password='testpass123',
        )
        comment = Comment.objects.create(
            author=user,
            content='Task test comment',
            like_count=3,
            reply_count=1,
        )

        # Call task directly (no broker needed in tests)
        recalculate_score_for_comment(str(comment.id))
        comment.refresh_from_db()
        assert comment.score > 0

    def test_rescore_stale_comments_returns_count(self):
        from django.contrib.auth import get_user_model
        from apps.comments.models import Comment
        from apps.ranking.tasks import rescore_stale_comments

        User = get_user_model()
        user = User.objects.create_user(
            email='batch@test.com',
            username='batchuser',
            password='testpass123',
        )
        Comment.objects.create(author=user, content='Batch 1')
        Comment.objects.create(author=user, content='Batch 2')

        result = rescore_stale_comments()
        assert result == 2