import django_filters
from apps.comments.models import Comment


class CommentFilter(django_filters.FilterSet):
    """
    [HARD-04] Filterable fields on the comment list endpoint.

    Usage:
      ?author_id=<uuid>
      ?created_after=2024-01-01
      ?created_before=2024-12-31
      ?is_flagged=true
      ?has_replies=true
    """
    author_id = django_filters.UUIDFilter(
        field_name='author__id',
        label='Filter by author UUID',
    )
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Comments created after this datetime (ISO 8601)',
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Comments created before this datetime (ISO 8601)',
    )
    is_flagged = django_filters.BooleanFilter(
        field_name='is_flagged',
        label='Filter flagged comments',
    )
    has_replies = django_filters.BooleanFilter(
        method='filter_has_replies',
        label='Filter comments that have at least one reply',
    )

    class Meta:
        model  = Comment
        fields = ['author_id', 'created_after', 'created_before', 'is_flagged']

    def filter_has_replies(self, queryset, name, value):
        if value:
            return queryset.filter(reply_count__gt=0)
        return queryset.filter(reply_count=0)