from services.nodes_service import contextualize_query, classify_query, generate_response, should_summarize, summarize_recent_messages, update_old_messages, should_update_old_messages, ChatState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


workflow = StateGraph(ChatState)
workflow.add_node("contextualize_query", contextualize_query)
workflow.add_node("classify_query", classify_query)
workflow.add_node("generate_response", generate_response)
workflow.add_node("summarize_recent_messages", summarize_recent_messages)
workflow.add_node("update_old_messages", update_old_messages)

workflow.add_edge(START, "contextualize_query")
workflow.add_edge("contextualize_query", "classify_query")
workflow.add_edge("classify_query", "generate_response")
workflow.add_conditional_edges("generate_response", should_summarize)
workflow.add_conditional_edges("summarize_recent_messages", should_update_old_messages)
workflow.add_edge("update_old_messages", END)

memory = MemorySaver()
chat_graph = workflow.compile(checkpointer=memory)