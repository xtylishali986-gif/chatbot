# escalations.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)


def get_open_escalation(client_id: str, session_id: str) -> dict | None:
    response = (
        supabase.table("escalations")
        .select("*")
        .eq("client_id", client_id)
        .eq("session_id", session_id)
        .eq("status", "open")
        .execute()
    )
    return response.data[0] if response.data else None


def flag_for_human(client_id: str, session_id: str, reason: str, conversation_summary: str) -> dict:
    existing = get_open_escalation(client_id, session_id)
    if existing:
        return {**existing, "already_escalated": True}
    result = (
        supabase.table("escalations")
        .insert({"client_id": client_id, "session_id": session_id, "reason": reason,
                 "conversation_summary": conversation_summary, "status": "open"})
        .execute()
    )
    return {**result.data[0], "already_escalated": False}