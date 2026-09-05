# products.py
# WHAT: Product search, now backed by Supabase instead of a hardcoded list,
# and ALWAYS scoped to a single client_id.
# WHY: This is the same function signature change discussed back in Phase 2 —
# we said the mock data would eventually be swapped for a real database
# without touching the agent code. This is that swap.

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)


def search_products(
    client_id: str,
    category: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = True,
) -> list[dict]:
    # WHY: client_id filter is ALWAYS applied first and is never optional —
    # this is the actual security boundary of multi-tenancy. Every other
    # filter is optional; this one never is.
    query = supabase.table("products").select("*").eq("client_id", client_id)

    if category:
        query = query.ilike("category", category)
    if max_price is not None:
        query = query.lte("price", max_price)
    if in_stock_only:
        query = query.eq("in_stock", True)

    response = query.execute()
    return response.data