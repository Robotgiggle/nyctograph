import stripe
from fastapi import Request, HTTPException
from pydantic import BaseModel

from .models import Researcher
from .config import settings

client = stripe.StripeClient(settings.STRIPE_API_KEY)

def create_checkout_session(res: Researcher, rows_accessed: int, success_path: str):
    costCents = max(50, rows_accessed*settings.ROW_PRICE_CENTS)
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
            "success_url": settings.APP_DOMAIN + success_path
        }
    )
    return session

async def get_checkout_info(request: Request):
    # extract webhook payload and signature header
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if signature is None: 
        raise HTTPException(status_code=403, detail="Missing signature header.")
    
    # verify signature
    try:
        event = client.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=403, detail="Signature verification failed.")
    
    # transfer relevant info to pydantic model
    checkoutSes = client.v1.checkout.sessions.retrieve(event["data"]["object"]["id"])
    if checkoutSes.metadata is None:
        raise HTTPException(status_code=400, detail="Checkout metadata is missing.")
    info = CheckoutModel(
        session_id=checkoutSes.id,
        payment_status=checkoutSes.payment_status,
        **checkoutSes.metadata.to_dict()
    )

    return info

class CheckoutModel(BaseModel):
    session_id: str
    payment_status: str
    res_id: str
    filters: str
    rows: int
    fulfilled: bool

    def mark_fulfilled(self):
        client.v1.checkout.sessions.update(
            self.session_id, 
            params = {
                "metadata": {"fulfilled": "true"}
            }
        )