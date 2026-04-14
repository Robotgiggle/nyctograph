import resend
from typing import List
from fastapi import BackgroundTasks
from urllib.parse import quote
from dotenv import load_dotenv
from os import getenv

from .jinja import template_string

load_dotenv(".env")

resend.api_key = getenv("RESEND_API_KEY")

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
    confirm_url = getenv("APP_DOMAIN", "") + "/signup/research/confirm?token=" + quote(token)
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