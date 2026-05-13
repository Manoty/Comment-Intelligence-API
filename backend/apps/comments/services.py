import logging
from django.db import transaction
from django.db.models import F
from django.core.exceptions import PermissionDenied, ValidationError

from .models import Comment

logger = logging.getLogger(__name__)


class CommentService:

    @staticmethod
    @transaction.atomic
    def create_comment(*, author, content: str) -> Comment:
        """
        [COMMENT-02a] Create root-level comment.
        """
        if not content or not content.strip():
            raise ValidationError('Comment content cannot be empty.')

        comment = Comment.objects.create(
            author=author,
            content=content.strip(),
        )
        logger.info(f'Comment created: {comment.id} by user {author.id}')
        return comment

    @staticmethod
    @transaction.atomic
    def create_reply(*, author, parent_id, content: str) -> Comment:
        """
        [COMMENT-02b] Create a reply to an existing comment.
        Increments parent reply_count atomically.
        """
        if not content or not content.strip():
            raise ValidationError('Reply content cannot be empty.')

        try:
            parent = Comment.objects.get(id=parent_id, is_deleted=False)
        except Comment.DoesNotExist:
            raise ValidationError('Parent comment not found or has been deleted.')

        reply = Comment.objects.create(
            author=author,
            parent=parent,
            content=content.strip(),
        )

        # Atomic increment — safe under concurrent requests
        Comment.objects.filter(id=parent.id).update(reply_count=F('reply_count') + 1)

        logger.info(f'Reply created: {reply.id} -> parent: {parent.id}')
        return reply

    @staticmethod
    @transaction.atomic
    def edit_comment(*, comment_id, requesting_user, content: str) -> Comment:
        """
        [COMMENT-02c] Edit comment content. Author-only.
        """
        if not content or not content.strip():
            raise ValidationError('Comment content cannot be empty.')

        try:
            comment = Comment.objects.get(id=comment_id, is_deleted=False)
        except Comment.DoesNotExist:
            raise ValidationError('Comment not found.')

        if comment.author_id != requesting_user.id:
            raise PermissionDenied('You can only edit your own comments.')

        comment.content = content.strip()
        comment.save(update_fields=['content', 'updated_at'])

        logger.info(f'Comment edited: {comment.id} by user {requesting_user.id}')
        return comment

    @staticmethod
    @transaction.atomic
    def delete_comment(*, comment_id, requesting_user) -> None:
        """
        [COMMENT-02d] Soft delete. Content wiped, record kept for thread integrity.
        Decrements parent reply_count if this is a reply.
        """
        try:
            comment = Comment.objects.get(id=comment_id, is_deleted=False)
        except Comment.DoesNotExist:
            raise ValidationError('Comment not found.')

        if comment.author_id != requesting_user.id:
            raise PermissionDenied('You can only delete your own comments.')

        comment.is_deleted = True
        comment.content = '[deleted]'
        comment.save(update_fields=['is_deleted', 'content', 'updated_at'])

        if comment.parent_id:
            Comment.objects.filter(id=comment.parent_id).update(
                reply_count=F('reply_count') - 1
            )

        logger.info(f'Comment soft-deleted: {comment.id} by user {requesting_user.id}')