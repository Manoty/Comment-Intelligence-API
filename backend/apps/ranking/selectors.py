from django.db.models import QuerySet, F, FloatField, ExpressionWrapper
from apps.comments.models import Comment


class RankingSelector:

    @staticmethod
    def get_comments_by_sort(sort: str) -> QuerySet:
        """
        [RANK-03a] Return root comments ordered by the requested sort mode.
        All modes filter deleted comments and top-level only.
        """
        base_qs = (
            Comment.objects
            .filter(parent__isnull=True, is_deleted=False)
            .select_related('author')
            .prefetch_related('replies')
        )

        sort_dispatch = {
            'latest':        lambda qs: qs.order_by('-created_at'),
            'top':           lambda qs: qs.order_by('-like_count'),
            'most_relevant': lambda qs: qs.order_by('-score'),
            'trending':      RankingSelector._apply_trending_sort,
        }

        sorter = sort_dispatch.get(sort, sort_dispatch['latest'])
        return sorter(base_qs)

    @staticmethod
    def _apply_trending_sort(qs: QuerySet) -> QuerySet:
        """
        [RANK-03b] Trending sort: order by score descending, filtered to
        comments created in the last 48 hours.
        Trending is time-windowed — old comments cannot trend.
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(hours=48)
        return (
            qs.filter(created_at__gte=cutoff)
            .order_by('-score', '-created_at')
        )

    @staticmethod
    def get_comments_needing_rescore(batch_size: int = 500) -> QuerySet:
        """
        [RANK-03c] Fetch comments whose score may be stale.
        Used by the Celery periodic task.
        Orders by oldest rescore first.
        """
        return (
            Comment.objects
            .filter(is_deleted=False)
            .order_by('updated_at')
            [:batch_size]
        )