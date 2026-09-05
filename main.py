# main.py
# WHAT: FastAPI backend using the full 5-tool LangGraph agent, now MULTI-TENANT.
# WHY (Phase 8 update): every request must now carry a valid api_key, which
# gets resolved to a client_id BEFORE anything else runs. That client_id is
# threaded through the agent so every tool call is scoped to the correct
# client's data — this is the actual security boundary of multi-tenancy,
# same rigor as the Phase 4 order-lookup identity check.

import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import RateLimitError

from agent import agent_graph
from leads import get_lead
from clients import resolve_client

load_dotenv()

app = FastAPI(title="Ecommerce Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# WHY: Sessions are now keyed by (client_id, session_id) together — a
# session_id alone is no longer guaranteed unique across different clients,
# since two different businesses' widgets could theoretically generate the
# same UUID (astronomically unlikely, but the composite key is the correct,
# principled fix rather than relying on luck).
SESSIONS: dict[tuple[str, str], list[dict]] = {}

SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant for {store_name}. "
    "When asked about products, you may ONLY mention products that "
    "appear in the search tool's JSON results — NEVER invent, assume, "
    "or supplement with products not explicitly present in tool output. "
    "When asked about returns, shipping, or warranty policies, you MUST "
    "use the policy retrieval tool and answer ONLY based on the "
    "retrieved text — NEVER invent policy details from general knowledge. "
    "When asked about order status or tracking, you MUST have BOTH the "
    "order number AND the email used for that order before calling the "
    "order lookup tool — if either is missing, ask the customer for it "
    "first. NEVER guess, assume, or make up an order number or email "
    "on the customer's behalf. If the lookup tool returns no result, "
    "tell the customer honestly that no matching order was found and "
    "suggest they double-check their order number and email. "
    "If the customer shows genuine interest in a product (asking about "
    "buying, pricing, or availability), naturally ask for their name and "
    "email so the store can follow up — save each piece of info as soon "
    "as they share it using the lead capture tool. NEVER ask for contact "
    "info during a simple FAQ or policy question, and NEVER ask again "
    "for information already shown to you as known customer info. "
    "If a customer is frustrated or upset, especially repeatedly, or "
    "explicitly asks for a human, or has a request no tool can resolve "
    "(like a policy exception), use the escalation tool to flag the "
    "conversation for a human agent. If the escalation tool tells you "
    "the conversation was ALREADY escalated, do not call it again — "
    "just calmly reassure the customer a team member will follow up "
    "soon, without repeating the full transfer message every time. "
    "Tell the customer honestly that you're connecting them with a "
    "team member — NEVER pretend to resolve something you cannot "
    "actually fix, and never make promises about refunds or exceptions "
    "the policy doesn't support. "
    "If retrieved results don't clearly answer the question, say so "
    "honestly instead of guessing."
)

MAX_HISTORY_MESSAGES = 12


class ChatRequest(BaseModel):
    api_key: str  # NEW — required on every request
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


def get_or_create_session(client_id: str, session_id: str | None, store_name: str) -> str:
    key_exists = session_id and (client_id, session_id) in SESSIONS
    if key_exists:
        return session_id
    new_id = str(uuid.uuid4())
    system_prompt = {
        "role": "system",
        "content": SYSTEM_PROMPT_TEMPLATE.format(store_name=store_name),
    }
    SESSIONS[(client_id, new_id)] = [system_prompt]
    return new_id


def truncate_history(messages: list[dict]) -> list[dict]:
    if len(messages) <= MAX_HISTORY_MESSAGES + 1:
        return messages
    return [messages[0]] + messages[-MAX_HISTORY_MESSAGES:]


def build_lead_reminder(client_id: str, session_id: str) -> dict | None:
    lead = get_lead(client_id=client_id, session_id=session_id)
    if not lead:
        return None

    known = {k: v for k, v in lead.items() if k in ("name", "email", "phone", "interest") and v}
    if not known:
        return None

    facts = ", ".join(f"{k}={v}" for k, v in known.items())
    return {
        "role": "system",
        "content": f"Known info about this customer so far (already saved): {facts}. Do not ask for these again.",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # WHY: This is the FIRST thing that happens — resolve and validate the
    # API key before touching any session or client data. An invalid key
    # is rejected immediately with 401, never silently falling through to
    # some default client's data.
    client = resolve_client(request.api_key)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid API key")
    client_id = client["client_id"]
    store_name = client["store_name"]

    session_id = get_or_create_session(client_id, request.session_id, store_name)

    full_history = SESSIONS[(client_id, session_id)]
    full_history.append({"role": "user", "content": request.message})

    model_context = truncate_history(full_history)

    reminder = build_lead_reminder(client_id, session_id)
    if reminder:
        model_context = model_context + [reminder]

    try:
        result = agent_graph.invoke({
            "messages": model_context,
            "session_id": session_id,
            "client_id": client_id,  # NEW — threaded into agent state
        })
    except RateLimitError:
        full_history.pop()
        raise HTTPException(
            status_code=503,
            detail="I'm experiencing high demand right now. Please try again in a few minutes.",
        )

    updated_messages = result["messages"]
    new_messages = updated_messages[len(model_context):]
    full_history.extend(new_messages)
    SESSIONS[(client_id, session_id)] = full_history

    print("\n" + "=" * 60)
    print(f"[client_id={client_id}]")
    for m in new_messages:
        print(f"[{m['role']}] tool_calls={m.get('tool_calls')} content={m.get('content')}")
    print("=" * 60 + "\n")

    reply = next(
        (m["content"] for m in reversed(new_messages) if m["role"] == "assistant" and m["content"]),
        "I'm not sure how to respond to that.",
    )

    return ChatResponse(session_id=session_id, reply=reply)


@app.get("/health")
def health():
    return {"status": "ok"}