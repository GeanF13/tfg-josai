from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from persistence.chromadb_client import ChromaDBClient
from langgraph.graph import MessageState
from langchain_ollama import ChatOllama
from services.query_classifier_service import QueryClassifierService
from langgraph.graph import StateGraph, START, END
from services.prompt_service import PromptService


llm = ChatOllama(
    model = "llama3.2",
    temperature = 0
)

class ChatState(MessageState):
    subject_id: str
    category: str
    summary: str
    user_query_temporal: str

def contextualize_query(state: ChatState):
    query_classifier = QueryClassifierService()
    messages = state["messages"]
    summary = state.get("summary", "")
    
    if len(messages) > 1 :
        if summary:
            system_message = f"Dado un historial de chat, el resumen de la conversación anterior y la última pregunta del usuario, la cual podría hacer referencia al contexto presente en dicho historial y resumen, formula una pregunta independiente que pueda ser comprendida sin necesidad del historial ni del resumen. NO respondas la pregunta, solo reformúlala si es necesario o, en caso contrario, déjala tal como está.
            Resumen de la conversación anterior: {summary}"
            
        else:
            system_message = ("Dado un historial de chat y la última pregunta del usuario, la cual podría hacer referencia al contexto presente en dicho historial,"
            "formula una pregunta independiente que pueda ser comprendida sin necesidad del historial." 
            "NO respondas la pregunta, solo reformúlala si es necesario o, en caso contrario, déjala tal como está.")
        
        messages = [SystemMessage(content=system_message)] + state["messages"]
        user_query_temp = llm.invoke(messages)
        category = query_classifier.classify_query(user_query_temp)
    
    else:
        user_query_temp = state["messages"][-1].content
        category = query_classifier.classify_query(user_query_temp)
    
    return {"user_query_temporal": user_query_temp, "category": category}        

def classify_query(state: ChatState):
    category = state["category"]
    match category:
        case "A":
            return "generate_response"
        case "BP" | "BG" | "BE" | "BT":
            return "generate_response"
        case "C" | _:
            return END

def generate_response(state: ChatState):
    prompt_service = PromptService()
    category = state["category"]
    subject_id = state["subject_id"]
    user_query_temp = state["user_query_temporal"]
    messages = state["messages"]
    match category:
        case "A":
            response = prompt_service.query_type_a(messages, subject_id, user_query_temp)
        case "BP" | "BG" | "BE" | "BT":
            response = prompt_service.query_type_b(category[1], subject_id, user_query_temp)
    return {"messages": response}

def should_summarize(state: ChatState):
    pass

def summarize_conversation(state: ChatState):
    pass