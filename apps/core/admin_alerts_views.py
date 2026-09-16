"""JSON endpoint для дзвіночка сповіщень у адмінці."""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.core.admin_alerts import get_alerts_payload


@staff_member_required
@require_GET
def admin_alerts_json(request):
    return JsonResponse(get_alerts_payload())
