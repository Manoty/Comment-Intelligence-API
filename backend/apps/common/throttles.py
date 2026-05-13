from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class CommentCreateThrottle(UserRateThrottle):
    """
    [HARD-06a] Tighter limit for comment creation.
    30 comments per hour per authenticated user.
    """
    scope = 'comment_create'


class FlagThrottle(UserRateThrottle):
    """
    [HARD-06b] Flag endpoint — 50 flags per hour per user.
    Prevents mass-flag abuse.
    """
    scope = 'flag'


class BurstAnonThrottle(AnonRateThrottle):
    """
    [HARD-06c] Tighter burst limit for unauthenticated reads.
    Falls back to 'anon' scope defined in settings.
    """
    scope = 'anon'