import resend
from typing import List
from urllib.parse import quote

from .jinja import template_string
from .config import settings

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

def send_research_approval(recipient: str, name: str, token: str):
    confirm_url = settings.APP_DOMAIN + "/signup/research/confirm?token=" + quote(token)
    context = {"name": name, "url": confirm_url}
    send_email(
        [recipient],
        "Research account approved",
        template_string("email/research_approval.html", context)
    )

def send_research_denial(recipient: str, name: str, req_msg: str, deny_msg: str):
    context = {"name": name, "req_msg": req_msg, "deny_msg": deny_msg}
    send_email(
        [recipient],
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