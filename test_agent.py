# test_agent.py
from agent import agent_graph

result = agent_graph.invoke({
    "messages": [
        {
            "role": "system",
            "content": (
                "You are a store product assistant. You may ONLY mention products "
                "that appear in the search tool's JSON results. NEVER invent, "
                "assume, or supplement with products not explicitly present in "
                "the tool output. If the results are limited, say so honestly "
                "instead of adding more items."
            ),
        },
        {"role": "user", "content": "Show me shoes under $100"},
    ]
})

for msg in result["messages"]:
    print(f"--- {msg['role']} ---")
    print(msg.get("content"))
    print()