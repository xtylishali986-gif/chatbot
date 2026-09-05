# test_escalations.py
from escalations import flag_for_human

result = flag_for_human(
    session_id="test-session-999",
    reason="Customer angry about damaged item, policy doesn't cover their case",
    conversation_summary="Customer received a torn jacket, wants a refund but item was marked Final Sale. Policy says no returns on Final Sale items, but item arrived damaged.",
)
print(result)