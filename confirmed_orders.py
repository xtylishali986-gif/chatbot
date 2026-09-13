# confirmed_orders.py
# WHAT: Logs a confirmed order to Supabase and notifies the client's n8n
# webhook (if configured), which handles however THAT business wants to
# be notified (Slack, email, WhatsApp — n8n's job, not ours).
import os
import httpx
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def confirm_order(
    client_id: str,
    session_id: str,
    product_name: str,
    quantity: int,
    customer_name: str,
    customer_email: str,
    shipping_address: str,
    customer_phone: str ,
) -> dict:
    result = (
        supabase.table("confirmed_orders")
        .insert({
            "client_id": client_id,
            "session_id": session_id,
            "product_name": product_name,
            "quantity": quantity,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "shipping_address": shipping_address,
            "status": "pending",
        })
        .execute()
    )
    order_row = result.data[0]

    # WHY: notify n8n only if this client has configured a webhook — keeps
    # the flow optional per client, no crash if it's not set up yet.
    client_resp = supabase.table("clients").select("n8n_webhook_url").eq("client_id", client_id).execute()
    webhook_url = client_resp.data[0].get("n8n_webhook_url") if client_resp.data else None
    if webhook_url:
        try:
            httpx.post(webhook_url, json=order_row, timeout=5)
        except Exception as e:
            print(f"[confirm_order] Failed to notify n8n: {e}")

    return order_row