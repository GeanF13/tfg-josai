from fastapi import APIRouter, HTTPException, UploadFile, File
from services.embedding_service import EmbeddingService
from persistence.supabase_client import SupabaseClient

router = APIRouter()

@router.post("/upload-faq/{subject_id}")
async def upload_faq(subject_id: str, faq: UploadFile = File(...)):
    # Check if the file is a PDF
    if not faq.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    
    # Read the file
    file_bytes = await faq.read()
    
    # Initialize the Supabase client
    supabase_client = SupabaseClient()
    
    # Process the file
    try:
        embedding_service = EmbeddingService(subject_id)
        embedding_service.process_faq(file_bytes)
        return {"message": "FAQ procesada correctamente"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))