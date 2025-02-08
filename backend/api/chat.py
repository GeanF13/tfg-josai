from fastapi import APIRouter, HTTPException
from services.prompt_service import PromptService
from services.query_classifier_service import QueryClassifierService
from models.chat_request import ChatRequest

router = APIRouter()
prompt_service = PromptService()
query_classifier = QueryClassifierService()

@router.post("/chat/")
async def chat(request: ChatRequest):
    try:
        classification_result = query_classifier.classify_query(request.user_query)
        category = classification_result
        
        match category:
            case "A":
                response = prompt_service.query_type_a(request.subject_id, request.user_query)
            case "BP" | "BG" | "BE" | "BT":
                response = prompt_service.query_type_b(category[1], request.subject_id, request.user_query)
            case "C" | _:
                response = "No tengo la capacidad de responder esa pregunta."
        return {"response": response, "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento del chat: {str(e)}")