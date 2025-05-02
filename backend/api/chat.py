from fastapi import APIRouter, HTTPException
from services.prompt_service import PromptService
from services.query_classifier_service import QueryClassifierService
from models.chat_request import ChatRequest
from langchain_core.messages import HumanMessage, AIMessage
from services.graph_workflow import chat_graph, memory
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
prompt_service = PromptService()
query_classifier = QueryClassifierService()

@router.post("/chat/")
async def chat(request: ChatRequest):
    try:
        # Si no se proporciona un thread_id, crear uno nuevo
        thread_id = request.thread_id if request.thread_id else f"thread_{uuid.uuid4()}"
        config = {"configurable": {"thread_id": thread_id}}
        
        print("EL THREAD ID ES: ", thread_id)
        
        # Convertir la consulta del usuario en un mensaje
        input_message = HumanMessage(content=request.user_query)
        
        # Buscar si hay una conversación previa guardada con este thread_id
        previous_state = memory.get(config)
        previous_state = chat_graph.get_state(config=config)
        
        if previous_state:
            # Si hay una conversación previa, añadir el nuevo mensaje a los mensajes recientes
            recent_messages = previous_state.values.get("recent_messages", [])
            
            # Añadir el nuevo mensaje
            recent_messages.append(input_message)
            
            # Invocar el grafo con los mensajes actualizados
            output = chat_graph.invoke({"recent_messages": recent_messages, "subject_id": request.subject_id}, config)
        else:
            # Si es la primera vez, iniciar una nueva conversación
            output = chat_graph.invoke({"recent_messages": [input_message], "subject_id": request.subject_id}, config)
        
        print("La lista de RECENT MESSAGES antes de invocar el grafo es: ")
        if previous_state:
            print(recent_messages)
                
        # Obtener la última respuesta
        if output["recent_messages"]:
            print("La lista de RECENT MESSAGES después de invocar el grafo es: ")
            print(output["recent_messages"])
            # Intentar obtener el último mensaje del asistente
            ai_messages = [m for m in output["recent_messages"] if isinstance(m, AIMessage)]
            if ai_messages:
                response_content = ai_messages[-1].content
            else:
                response_content = "No se pudo generar una respuesta."
            
            # Determinar la categoría (si la tienes disponible en el estado)
            category = output.get("category", "desconocida")
        else:
            response_content = "No se pudo generar una respuesta."
            category = "desconocida"
        
        # Devolver también el thread_id para que el cliente lo use en futuras peticiones
        return {"response": response_content, "category": category, "thread_id": thread_id}
    except Exception as e:
        logger.error(f"Error en el chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento del chat: {str(e)}")