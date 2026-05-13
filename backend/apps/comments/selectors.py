from django.db.models import QuerySet
from .models import Comment


class CommentSelector:

    @staticmethod
    def get_root_comments(sort: str = 'latest') -> QuerySet:
        """
        [COMMENT-03a] Fetch all non-deleted root comments with sort applied.
        """
        qs = (
            Comment.objects
            .filter(parent__isnull=True, is_deleted=False)
            .select_related('author')
            .prefetch_related('replies')
        )

        sort_map = {
            'latest':       '-created_at',
            'top':          '-like_count',
            'most_relevant':'-score',
            'trending':     '-score',   # Phase 3 will differentiate this
        }

        order_field = sort_map.get(sort, '-created_at')
        return qs.order_by(order_field)

    @staticmethod
    def get_comment_by_id(comment_id) -> Comment:
        """
        [COMMENT-03b] Fetch single comment with author. Returns None if not found.
        """
        try:
            return (
                Comment.objects
                .select_related('author')
                .get(id=comment_id, is_deleted=False)
            )
        except Comment.DoesNotExist:
            return None

    @staticmethod
    def get_replies(parent_id) -> QuerySet:
        """
        [COMMENT-03c] Fetch direct replies for a comment. Ordered oldest-first
        for natural thread reading order.
        """
        return (
            Comment.objects
            .filter(parent_id=parent_id, is_deleted=False)
            .select_related('author')
            .order_by('created_at')
        )