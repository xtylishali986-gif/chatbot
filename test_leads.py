# test_leads.py
# WHAT: Verifies incremental merging works — the actual point of this tool.
from leads import save_lead, get_lead

session = "test-session-001"

print("--- Call 1: only name ---")
print(save_lead(session_id=session, name="Ali Salman"))

print("\n--- Call 2: only email (name should NOT be lost) ---")
print(save_lead(session_id=session, email="ali@example.com"))

print("\n--- Call 3: only interest (name + email should STILL be present) ---")
print(save_lead(session_id=session, interest="Trail Runner Pro shoes"))

print("\n--- Final state via get_lead ---")
print(get_lead(session))