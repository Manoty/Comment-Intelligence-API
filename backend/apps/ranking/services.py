import logging
import math
from datetime import datetime, timezone
from django.db import transaction

logger = logging.getLogger(__name__)


# --- Scoring weights (tune here, not in logic) ---
WEIGHT_LIKES = 2.0
WEIGHT_REPLIES = 3.0
WEIGHT_VELOCITY = 1.5
DECAY_GRAVITY = 1.8       # Higher = faster decay (Reddit uses 1.8)
TRENDING_VELOCITY_BOOST = 3.0
TRENDING_DECAY_COMPRESSION = 0.5


class CommentRankingService:

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @classmethod
    def recalculate_comment_score(cls, comment) -> float:
        """
        [RANK-02a] Compute and persist score for a single comment.
        Returns the new score.
        """
        score = cls.compute_score(comment, mode='most_relevant')

        from apps.comments.models import Comment
        Comment.objects.filter(id=comment.id).update(score=score)

        logger.debug(f'Score updated: comment={comment.id} score={score:.4f}')
        return score

    @classmethod
    def recalculate_trending_score(cls, comment) -> float:
        """
        [RANK-02b] Compute trending-specific score.
        Stored separately via query ordering — not persisted to score field.
        Used by selectors to sort trending feed.
        """
        return cls.compute_score(comment, mode='trending')

    # ------------------------------------------------------------------
    # Core formula assembler
    # ------------------------------------------------------------------

    @classmethod
    def compute_score(cls, comment, mode: str = 'most_relevant') -> float:
        """
        [RANK-02c] Assemble final score from individual factors.
        """
        likes       = cls._likes_score(comment.like_count)
        replies     = cls._replies_score(comment.reply_count)
        velocity    = cls._engagement_velocity(comment)
        decay       = cls._time_decay(comment, mode=mode)

        if mode == 'trending':
            score = (
                likes
                + replies
                + (velocity * TRENDING_VELOCITY_BOOST)
                - (decay * TRENDING_DECAY_COMPRESSION)
            )
        else:
            score = (
                likes
                + replies
                + (velocity * WEIGHT_VELOCITY)
                - decay
            )

        return round(max(score, 0.0), 6)  # score floor at 0

    # ------------------------------------------------------------------
    # Individual scoring factors
    # ------------------------------------------------------------------

    @staticmethod
    def _likes_score(like_count: int) -> float:
        """
        [RANK-02d] Raw likes contribution.
        """
        return WEIGHT_LIKES * like_count

    @staticmethod
    def _replies_score(reply_count: int) -> float:
        """
        [RANK-02e] Reply depth contribution.
        Replies signal conversation value, weighted higher than likes.
        """
        return WEIGHT_REPLIES * reply_count

    @staticmethod
    def _engagement_velocity(comment) -> float:
        """
        [RANK-02f] Engagement rate per hour since posting.
        Rewards comments gaining traction quickly.
        Formula: (likes + replies) / hours_alive (floor 1hr)
        """
        now = datetime.now(timezone.utc)
        created = comment.created_at

        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        hours_alive = max((now - created).total_seconds() / 3600, 1.0)
        total_engagement = comment.like_count + comment.reply_count

        return round(total_engagement / hours_alive, 6)

    @staticmethod
    def _time_decay(comment, mode: str = 'most_relevant') -> float:
        """
        [RANK-02g] Penalty that grows as a comment ages.
        Uses a logarithmic decay curve (same family as HN/Reddit ranking).

        Formula: log(hours_alive + 1) ^ gravity

        most_relevant: full gravity applied
        trending: gravity compressed — recent comments penalised less
        """
        now = datetime.now(timezone.utc)
        created = comment.created_at

        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        hours_alive = max((now - created).total_seconds() / 3600, 1.0)
        gravity = (
            DECAY_GRAVITY * TRENDING_DECAY_COMPRESSION
            if mode == 'trending'
            else DECAY_GRAVITY
        )

        return round(math.log(hours_alive + 1) ** gravity, 6)