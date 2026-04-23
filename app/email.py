import resend
from typing import List
from urllib.parse import quote

from .jinja import template_string
from .config import settings
from .models import ResearchRequest

resend.api_key = settings.RESEND_API_KEY

def send_email(recipients: List[str], subject: str, body_html: str):
    params: resend.Emails.SendParams = {
        "from": "Nyctograph <noreply@nyctograph.org>",
        "to": recipients,
        "subject": subject,
        "html": body_html,
    }
    email = resend.Emails.send(params)
    return email

def send_research_approval(resReq: ResearchRequest):
    if not resReq.token: 
        raise ValueError("Cannot send an approval email without a token!")
    confirm_url = settings.APP_DOMAIN + "/signup/research/confirm?token=" + quote(resReq.token)
    context = {"name": resReq.name, "url": confirm_url}
    send_email(
        [resReq.email],
        "Research account approved",
        template_string("email/research_approval.html", context)
    )

def send_research_denial(resReq: ResearchRequest, deny_msg: str):
    context = {"name": resReq.name, "req_msg": resReq.reason, "deny_msg": deny_msg}
    send_email(
        [resReq.email],
        "Research account request denied",
        template_string("email/research_denial.html", context)
    )

def send_data_access_notifs(userRows, instID: str, instName: str, count: int):
    instURL = f"https://ror.org/{instID}"
    for row in userRows:
        context = {
            "name": row[1], "instName": instName, 
            "instURL": instURL, "count": count, 
            "domain": settings.APP_DOMAIN
        }
        send_email(
            [row[0]],
            "Your data was accessed",
            template_string("email/data_access_notif.html", context)
        )