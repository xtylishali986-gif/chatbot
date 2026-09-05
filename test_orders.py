# test_orders.py
# WHAT: Standalone test of the identity-checked order lookup, BEFORE wiring
# into the agent — same debugging discipline as previous phases.

from orders import lookup_order

print("--- Correct order_number + correct email ---")
print(lookup_order("ORD-1001", "ali.test@example.com"))

print("\n--- Correct order_number + WRONG email (should be None) ---")
print(lookup_order("ORD-1001", "wrong.person@example.com"))

print("\n--- Nonexistent order_number ---")
print(lookup_order("ORD-9999", "ali.test@example.com"))