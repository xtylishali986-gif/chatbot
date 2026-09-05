# leads.py
# WHAT: Incremental lead capture — saves/updates partial customer info
# tied to a (client_id, session_id) pair, in Supabase.
# WHY (Phase 8 update): client_id added to BOTH save_lead and get_lead —
# a session_id alone is no longer sufficient to identify a lead, since
# different clients could theoretically have colliding session_ids.

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)


def save_lead(
    client_id: str,
    session_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    interest: str | None = None,
) -> dict:
    existing = (
        supabase.table("leads")
        .select("*")
        .eq("client_id", client_id)
        .eq("session_id", session_id)
        .execute()
    )

    current = existing.data[0] if existing.data else {}

    merged = {
        "client_id": client_id,
        "session_id": session_id,
        "name": name or current.get("name"),
        "email": email or current.get("email"),
        "phone": phone or current.get("phone"),
        "interest": interest or current.get("interest"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = (
        supabase.table("leads")
        .upsert(merged, on_conflict="client_id,session_id")
        .execute()
    )

    return result.data[0]


def get_lead(client_id: str, session_id: str) -> dict | None:
    # WHY: Now filters by BOTH client_id and session_id — matches the
    # composite primary key set up on the leads table in Step 1.
    response = (
        supabase.table("leads")
        .select("*")
        .eq("client_id", client_id)
        .eq("session_id", session_id)
        .execute()
    )
    return response.data[0] if response.data else None