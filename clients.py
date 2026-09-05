# clients.py
# WHAT: Resolves an API key (sent by a client's widget) into a client_id.
# WHY: This is the SINGLE gatekeeping point for multi-tenancy — every
# request must pass through this before touching any client-specific data.
# If the key is invalid, we stop here rather than letting a bad request
# reach any tool.

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)


def resolve_client(api_key: str) -> dict | None:
    """Look up a client by their API key. Returns None if invalid —
    the caller (main.py) must treat that as a hard rejection, not a
    fallback to some default client."""
    response = (
        supabase.table("clients")
        .select("*")
        .eq("api_key", api_key)
        .execute()
    )
    return response.data[0] if response.data else None
