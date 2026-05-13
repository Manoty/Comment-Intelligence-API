# Add import at top
from apps.common.throttles import FlagThrottle

class FlagCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        return [FlagThrottle()]

    # rest of method unchanged