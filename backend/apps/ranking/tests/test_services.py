import pytest
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from apps.ranking.services import (
    CommentRankingService,
    WEIGHT_LIKES,
    WEIGHT_REPLIES,
    WEIGHT_VELOCITY,
    DECAY_GRAVITY,
)


def make_mock_comment(
    like_count=0,
    reply_count=0,
    hours_old=1,
):
    """Build a mock comment with controlled age."""
    comment = MagicMock()
    comment.like_count = like_count
    comment.reply_count = reply_count
    comment.created_at = datetime.now(timezone.utc) - timedelta(hours=hours_old)
    return comment


class TestLikesScore:
    def test_zero_likes(self):
        assert CommentRankingService._likes_score(0) == 0.0

    def test_positive_likes(self):
        assert CommentRankingService._likes_score(10) == WEIGHT_LIKES * 10


class TestRepliesScore:
    def test_zero_replies(self):
        assert CommentRankingService._replies_score(0) == 0.0

    def test_positive_replies(self):
        assert CommentRankingService._replies_score(5) == WEIGHT_REPLIES * 5

    def test_replies_outweigh_same_likes(self):
        assert (
            CommentRankingService._replies_score(1)
            > CommentRankingService._likes_score(1)
        )


class TestEngagementVelocity:
    def test_no_engagement(self):
        comment = make_mock_comment(like_count=0, reply_count=0, hours_old=5)
        assert CommentRankingService._engagement_velocity(comment) == 0.0

    def test_velocity_decreases_with_age(self):
        young = make_mock_comment(like_count=10, reply_count=5, hours_old=1)
        old = make_mock_comment(like_count=10, reply_count=5, hours_old=24)
        assert (
            CommentRankingService._engagement_velocity(young)
            > CommentRankingService._engagement_velocity(old)
        )

    def test_velocity_increases_with_engagement(self):
        low = make_mock_comment(like_count=1, reply_count=0, hours_old=2)
        high = make_mock_comment(like_count=50, reply_count=20, hours_old=2)
        assert (
            CommentRankingService._engagement_velocity(high)
            > CommentRankingService._engagement_velocity(low)
        )


class TestTimeDecay:
    def test_fresh_comment_low_penalty(self):
        comment = make_mock_comment(hours_old=1)
        penalty = CommentRankingService._time_decay(comment)
        assert penalty < 1.0

    def test_old_comment_high_penalty(self):
        young = make_mock_comment(hours_old=1)
        old = make_mock_comment(hours_old=168)  # 1 week
        assert (
            CommentRankingService._time_decay(old)
            > CommentRankingService._time_decay(young)
        )

    def test_trending_decay_less_than_relevant(self):
        comment = make_mock_comment(hours_old=10)
        trending_decay = CommentRankingService._time_decay(comment, mode='trending')
        relevant_decay = CommentRankingService._time_decay(comment, mode='most_relevant')
        assert trending_decay < relevant_decay


class TestComputeScore:
    def test_score_floor_is_zero(self):
        # A very old comment with no engagement should never go negative
        comment = make_mock_comment(like_count=0, reply_count=0, hours_old=10000)
        score = CommentRankingService.compute_score(comment)
        assert score >= 0.0

    def test_more_engagement_higher_score(self):
        low = make_mock_comment(like_count=1, reply_count=0, hours_old=2)
        high = make_mock_comment(like_count=20, reply_count=10, hours_old=2)
        assert (
            CommentRankingService.compute_score(high)
            > CommentRankingService.compute_score(low)
        )

    def test_trending_score_boosts_velocity(self):
        comment = make_mock_comment(like_count=5, reply_count=5, hours_old=1)
        trending = CommentRankingService.compute_score(comment, mode='trending')
        relevant = CommentRankingService.compute_score(comment, mode='most_relevant')
        # Trending boosts velocity weight — score should differ
        assert trending != relevant

    def test_score_is_float(self):
        comment = make_mock_comment(like_count=3, reply_count=1, hours_old=2)
        score = CommentRankingService.compute_score(comment)
        assert isinstance(score, float)


@pytest.mark.django_db
class TestRecalculateCommentScore:
    def test_score_written_to_db(self):
        from django.contrib.auth import get_user_model
        from apps.comments.models import Comment

        User = get_user_model()
        user = User.objects.create_user(
            email='rank@test.com',
            username='rankuser',
            password='testpass123',
        )
        comment = Comment.objects.create(
            author=user,
            content='Score me',
            like_count=5,
            reply_count=2,
        )
        new_score = CommentRankingService.recalculate_comment_score(comment)
        comment.refresh_from_db()
        assert comment.score == new_score
        assert comment.score > 0