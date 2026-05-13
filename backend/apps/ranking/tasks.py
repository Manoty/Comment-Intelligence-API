import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def recalculate_score_for_comment(self, comment_id: str):
    """
    [RANK-06a] Triggered after any write that affects scoring inputs.
    Retries up to 3 times on failure with 10s delay.
    """
    try:
        from apps.comments.models import Comment
        from apps.ranking.services import CommentRankingService

        comment = Comment.objects.get(id=comment_id, is_deleted=False)
        new_score = CommentRankingService.recalculate_comment_score(comment)
        logger.info(f'Score recalculated: comment={comment_id} score={new_score}')

    except Exception as exc:
        logger.error(f'Score recalc failed for {comment_id}: {exc}')
        raise self.retry(exc=exc)


@shared_task
def rescore_stale_comments():
    """
    [RANK-06b] Periodic task — rescores a batch of comments.
    Runs every 10 minutes via Celery Beat.
    Scores decay over time so periodic refresh keeps rankings accurate.
    """
    from apps.ranking.selectors import RankingSelector
    from apps.ranking.services import CommentRankingService

    comments = RankingSelector.get_comments_needing_rescore(batch_size=500)
    count = 0

    for comment in comments:
        try:
            CommentRankingService.recalculate_comment_score(comment)
            count += 1
        except Exception as e:
            logger.error(f'Batch rescore failed for comment {comment.id}: {e}')
            continue

    logger.info(f'Batch rescore complete: {count} comments updated')
    return count