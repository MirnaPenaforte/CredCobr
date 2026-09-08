import json
import os

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Notification
from .whatsapp import validate_webhook_signature


@csrf_exempt
def whatsapp_webhook(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        if request.GET.get("hub.verify_token") != os.getenv("META_WEBHOOK_VERIFY_TOKEN", ""):
            return JsonResponse({"detail": "invalid token"}, status=403)
        return JsonResponse({"challenge": request.GET.get("hub.challenge", "")})
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not validate_webhook_signature(request.body, signature):
        return JsonResponse({"detail": "invalid signature"}, status=403)
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "invalid payload"}, status=400)
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for status in value.get("statuses", []):
                message_id = status.get("id")
                notification = Notification.objects.filter(provider_message_id=message_id).first()
                if notification:
                    mapped = {"delivered": Notification.Status.DELIVERED, "read": Notification.Status.READ}
                    if status.get("status") in mapped:
                        notification.status = mapped[status["status"]]
                        notification.save(update_fields=["status", "updated_at"])
    return JsonResponse({"received": True})
