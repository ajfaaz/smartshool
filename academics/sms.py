import json
import logging
import re
from urllib import error, request
from urllib.parse import quote

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    api_key = getattr(settings, "TERMII_API_KEY", "").strip()
    if not api_key or not phone_number:
        return False

    endpoint = getattr(settings, "TERMII_BASE_URL", "https://api.termii.com/api/sms/send")
    sender_name = getattr(settings, "TERMII_SENDER_ID", "SmartSchool")
    payload = {
        "to": phone_number,
        "from": sender_name,
        "sms": message,
        "type": "plain",
        "channel": "generic",
        "api_key": api_key,
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15):
            return True
    except (error.URLError, error.HTTPError, TimeoutError) as exc:
        logger.warning("Termii SMS send failed for %s: %s", phone_number, exc)
        return False


def _normalize_phone_for_whatsapp(phone_number):
    digits = re.sub(r"\D", "", phone_number or "")
    if not digits:
        return ""
    if digits.startswith("0"):
        return f"234{digits[1:]}"
    if digits.startswith("234"):
        return digits
    return digits


def build_whatsapp_result_link(student):
    phone = _normalize_phone_for_whatsapp(student.parent_phone)
    if not phone:
        return ""
    message = (
        f"Dear Parent, {student.name}'s exam result has been uploaded. "
        "Login to SmartSchool Portal to view the result."
    )
    return f"https://wa.me/{phone}?text={quote(message)}"


def send_result_notification(student):
    message = (
        f"Dear Parent, {student.name}'s exam result has been uploaded. "
        "Login to SmartSchool Portal to view the result."
    )
    channel = getattr(settings, "PARENT_NOTIFICATION_CHANNEL", "whatsapp").strip().lower()
    if channel == "termii":
        sent = send_sms(student.parent_phone, message)
        if sent:
            return {"channel": "termii", "status": "sent", "url": ""}

    whatsapp_link = build_whatsapp_result_link(student)
    if whatsapp_link:
        return {"channel": "whatsapp", "status": "draft", "url": whatsapp_link}

    return {"channel": "none", "status": "failed", "url": ""}
