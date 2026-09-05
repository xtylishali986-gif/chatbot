# test_agent.py
# WHAT: Standalone test for agent.py's graph, using plain dict messages
# (Groq's native format) instead of LangChain message objects.

from agent import agent_graph

result = agent_graph.invoke({
    "messages": [{"role": "user", "content": "Show me shoes under $100"}]
})

for msg in result["messages"]:
    print(f"--- {msg['role']} ---")
    print(msg.get("content"))
    print()