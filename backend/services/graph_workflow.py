from services.node_service import contextualize_query, classify_query, generate_response, should_summarize, summarize_conversation, ChatState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


workflow = StateGraph(ChatState)
workflow.add_node("contextualize_query", contextualize_query)
workflow.add_node("generate_response", generate_response)
workflow.add_node("summarize_conversation", summarize_conversation)

workflow.add_edge(START, "contextualize_query")
workflow.add_conditional_edges("contextualize_query", classify_query)
workflow.add_conditional_edges("generate_response", should_summarize)
workflow.add_edge("summarize_conversation", END)


memory = MemorySaver()
chat_graph = workflow.compile(checkpointer=memory)