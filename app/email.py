from typing import List
import resend

# TODO: put this in an environment variable for security
resend.api_key = "re_afbMQGHk_iEL3SWZF47KntYfeBB51LhqQ"

def send_email(recipients: List[str], subject: str, body_html: str):
    params: resend.Emails.SendParams = {
        "from": "Nyctograph <noreply@nyctograph.org>",
        "to": recipients,
        "subject": subject,
        "html": body_html,
    }
    email = resend.Emails.send(params)
    return email