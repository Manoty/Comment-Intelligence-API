import uuid
from django.db import models
from django.conf import settings


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
    )

    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    # Ranking fields — written by CommentRankingService (Phase 3)
    score = models.FloatField(default=0.0)
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments_comment'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['score']),
            models.Index(fields=['parent']),
            models.Index(fields=['author']),
            models.Index(fields=['is_deleted']),
            # Composite: most common query pattern (active top-level comments by score)
            models.Index(fields=['parent', 'is_deleted', 'score']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment({self.id}) by {self.author_id}'

    @property
    def is_reply(self):
        return self.parent_id is not None

    @property
    def is_root(self):
        return self.parent_id is None