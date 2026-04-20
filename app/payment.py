import stripe
from dotenv import load_dotenv
from os import getenv
from fastapi import HTTPException

from .models import Researcher

load_dotenv(".env")

client = stripe.StripeClient(api_key=getenv("STRIPE_API_KEY", ""))
webhook_secret = getenv("STRIPE_WEBHOOK_SECRET", "")

def create_checkout_session(res: Researcher, rows_accessed: int, success_path: str):
    costCents = max(50, rows_accessed)
    session = client.v1.checkout.sessions.create(
        params = {
            "line_items": [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": costCents,
                    "product_data": {
                        "name": f"Nyctograph Data ({rows_accessed} rows)"
                    }
                },
                "quantity": 1
            }],
            "metadata": {
                "res_id": str(res.id),
                "filters": res.pending_filters or "",
                "rows": str(rows_accessed),
                "fulfilled": "false"
            },
            "mode": "payment",
            "success_url": getenv("APP_DOMAIN", "")+success_path
        }
    )
    return session

def get_checkout_session(payload: str|bytes, signature: str):
    try:
        event = client.construct_event(payload, signature, webhook_secret)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=403, detail="Signature verification failed.")
    checkSesID = event["data"]["object"]["id"]
    return client.v1.checkout.sessions.retrieve(checkSesID)

def mark_fulfilled(check_ses: stripe.checkout.Session):
    client.v1.checkout.sessions.update(
        check_ses.id, 
        params = {
            "metadata": {"fulfilled": "true"}
        }
    )