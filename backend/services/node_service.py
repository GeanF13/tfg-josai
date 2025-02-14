from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from persistence.chromadb_client import ChromaDBClient
from langgraph.graph import MessagesState
from langchain_ollama import ChatOllama
from services.query_classifier_service import QueryClassifierService
from langgraph.graph import StateGraph, START, END
from services.prompt_service import PromptService


llm = ChatOllama(
    model = "deepseek-r1:8b",
    temperature = 0
)

class ChatState(MessagesState):
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
            system_message = f"Dado un historial de chat, el resumen de la conversación anterior y la última pregunta del usuario, la cual podría hacer referencia al contexto presente en dicho historial y resumen, formula una pregunta independiente que pueda ser comprendida sin necesidad del historial ni del resumen. NO respondas la pregunta, solo reformúlala si es necesario o, en caso contrario, déjala tal como está. Resumen de la conversación anterior: {summary}"
            
        else:
            system_message = ("Dado un historial de chat y la última pregunta del usuario, la cual podría hacer referencia al contexto presente en dicho historial,"
            "formula una pregunta independiente que pueda ser comprendida sin necesidad del historial." 
            "NO respondas la pregunta, solo reformúlala si es necesario o, en caso contrario, déjala tal como está.")
        
        messages = [SystemMessage(content=system_message)] + state["messages"]
        response = llm.invoke(messages)
        user_query_temp = response.content
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
    summary = state.get("summary", "")
    match category:
        case "A":
            response = prompt_service.query_type_a(summary, messages, subject_id, user_query_temp)
        case "BP" | "BG" | "BE" | "BT":
            response = prompt_service.query_type_b(category[1], summary, messages, subject_id, user_query_temp)
    return {"messages": response}

def should_summarize(state: ChatState):
    messages = state["messages"]
    
    if len(messages) > 6:
        return "summarize_conversation"
    else:
        return END

def summarize_conversation(state: ChatState):
    summary = state.get("summary", "")

    # Create our summarization prompt
    if summary:

        # If a summary already exists, add it to the prompt
        summary_message = (
            f"Este es un resumen de la conversación hasta este momento: {summary}\n\n"
            "Extiende el resumen teniendo en cuenta los nuevos mensajes de la conversación, dando mayor relevancia a los mensajes o datos numéricos para que haya un seguimiento coherente de la conversación."
        )

    else:
        # If no summary exists, just create a new one
        summary_message = "Crea un resumen de la conversación hasta este momento, dando mayor relevancia a los mensajes o datos numéricos para que haya un seguimiento coherente de la conversación."
    
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    #messages = state["messages"] + [SystemMessage(content=summary_message)]
    #messages = [SystemMessage(content=summary_message)] + state["messages"]
    response = llm.invoke(messages)
    
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}