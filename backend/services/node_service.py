from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from persistence.chromadb_client import ChromaDBClient
from langgraph.graph import MessagesState
from langchain_ollama import ChatOllama
from services.query_classifier_service import QueryClassifierService
from langgraph.graph import StateGraph, START, END
from services.prompt_service import PromptService
from services.utils import get_role
from langchain_deepseek import ChatDeepSeek
import os
#llm = ChatOllama(
#    model = "deepseek-r1:14b",
#    temperature = 0
#)

llm = ChatDeepSeek(
    model = "deepseek-reasoner",
    temperature = 0,
    api_key=os.getenv('DEEPSEEK_API_KEY')
)

class ChatState(MessagesState):
    subject_id: str
    category: str
    user_query_temporal: str
    recent_messages: list
    old_messages: list
    messages_count: int

def contextualize_query(state: ChatState):
    recent_messages = state["recent_messages"]
    old_messages = state.get("old_messages", [])
    
    if len(recent_messages) > 1 :
        system_message = """Dado un historial de chat y la última pregunta del usuario, la cual podría hacer referencia al contexto presente en dicho historial, formula una pregunta independiente que pueda ser comprendida sin necesidad del historial. 
        NO respondas la pregunta, solo reformúlala si es necesario o, en caso contrario, déjala tal como está."""
        
        if old_messages:
            chat_history = old_messages + recent_messages
            
        else:
            chat_history = recent_messages
        
        messages = [SystemMessage(content=system_message)] + chat_history
        print("ASI SE VE EL CONTEXTO DEL PRIMER NODO: ")
        print(messages)
        response = llm.invoke(messages)
        print("EL RESPONSE DE CONTEXTUALIZE QUERY ES: ")
        print(response)
        user_query_temp = response.content
    
    else:
        user_query_temp = state["recent_messages"][-1].content
    
    return {"user_query_temporal": user_query_temp}      

def classify_query(state: ChatState):
    query_classifier = QueryClassifierService()
    user_query_temp = state["user_query_temporal"]
    category = query_classifier.classify_query(user_query_temp)
    return {"category": category}

def generate_response(state: ChatState):
    prompt_service = PromptService()
    category = state["category"]
    subject_id = state["subject_id"]
    user_query_temp = state["user_query_temporal"]
    recent_messages = state["recent_messages"]
    old_messages = state.get("old_messages", [])
    messages_count = state.get("messages_count", 0)

    match category:
        case "A":
            response = prompt_service.query_type_a(old_messages, recent_messages, subject_id, user_query_temp)
        case "BP" | "BG" | "BE" | "BT":
            response = prompt_service.query_type_b(category[1], old_messages, recent_messages, subject_id, user_query_temp)
        case "C":
            response = AIMessage(content="No puedo responder a esa pregunta, por favor, formula una pregunta sobre la guía docente de la asignatura.")
    
    recent_messages.append(response)
    return {"recent_messages": recent_messages, "messages_count": messages_count+1}

def should_summarize(state: ChatState):
    recent_messages = state["recent_messages"]
    
    if len(recent_messages) > 6:
        return "summarize_recent_messages"
    else:
        return END

def summarize_recent_messages(state: ChatState):
    recent_messages = state["recent_messages"]
    
    if isinstance(recent_messages[0], SystemMessage):
        fragment1 = recent_messages[0]
        fragment2 = recent_messages[1]
        fragment3 = recent_messages[2]
        
        summary_message = f"""Genera un resumen conciso que integre la información clave de los tres fragmentos, manteniendo el contexto y la relevancia de cada uno, sin agregar información nueva ni detalles irrelevantes.
        A continuación se presentan tres fragmentos de la conversación:
        Fragmento 1 (Resumen anterior): {fragment1.content}
        Fragmento 2 (Mensaje Humano): {fragment2.content}
        Fragmento 3 (Mensaje IA): {fragment3.content}
        """
        
    else:
    
        fragment1 = recent_messages[0]
        fragment2 = recent_messages[1]
    
        summary_message = f"""Genera un resumen conciso que integre la información clave de ambos fragmentos, manteniendo el contexto y la relevancia de cada uno, sin agregar información nueva ni detalles irrelevantes.
    
        A continuación se presentan dos fragmentos de la conversación:
        Fragmento 1 (Mensaje Humano): {fragment1.content}
        Fragmento 2 (Mensaje IA): {fragment2.content}
        """
    
    response = llm.invoke(summary_message)
    print("EL RESPONSE DE SUMMARIZE RECENT MESSAGES ES: ")
    print(response)
    
    summary = SystemMessage(content="Resumen: " + response.content)
    
    recent_messages = [summary] + recent_messages[2:]
    
    return {"recent_messages": recent_messages}

def should_update_old_messages(state: ChatState):
    messages_count = state["messages_count"]
    
    if ((messages_count+1)%6==0 and messages_count > 6):
        return "update_old_messages"
    else:
        return END

def update_old_messages(state: ChatState):
    recent_messages = state["recent_messages"]
    old_messages = state.get("old_messages", [])
    
    if old_messages:
        old_messages.append(recent_messages[0])
    else:
        old_messages = [recent_messages[0]]
        
    recent_messages = recent_messages[1:]
    
    return {"old_messages": old_messages, "recent_messages": recent_messages}