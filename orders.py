# orders.py
# WHAT: Order lookup logic against a real Supabase table, with a mandatory
# two-factor identity check (order_number AND email must both match).
# WHY: Prevents leaking one customer's order details to anyone who merely
# guesses or knows an order number — a real security requirement, not
# an optional nicety, for any client-facing order tracking bot.

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)


def lookup_order(client_id: str, order_number: str, email: str) -> dict | None:
    """
    Look up an order by order_number, but ONLY return it if the provided
    email matches the email on file for that order.

    WHY both fields are required and checked together (not two separate
    queries): querying by order_number alone and THEN checking email in
    Python would still mean we fetched the wrong customer's full row into
    memory first. Filtering by BOTH fields in the query itself means a
    mismatched email returns literally zero rows from Supabase — the data
    never even leaves the database if the identity check fails.
    """
    # WHY: .ilike() for email = case-insensitive match, since customers
    # often type emails inconsistently (capitalization shouldn't cause a
    # legitimate lookup to fail).
    response = (
        supabase.table("orders")
        .select("*")
        .eq("client_id", client_id)
        .eq("order_number", order_number.strip().upper())
        .ilike("customer_email", email.strip())
        .execute()
    )
    return response.data[0] if response.data else None