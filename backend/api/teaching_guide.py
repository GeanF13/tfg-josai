from fastapi import APIRouter, HTTPException, UploadFile, File
from services.embedding_service import EmbeddingService
from persistence.supabase_client import SupabaseClient
from services.tables_service import TablesService

router = APIRouter()

@router.post("/upload-teaching-guide/")
async def upload_teaching_guide(guide: UploadFile = File(...)):
    # Check if the file is a PDF
    if not guide.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    
    # Read the file
    file_bytes = await guide.read()
    
    # Initialize the Supabase client
    supabase_client = SupabaseClient()
    
    table_service = TablesService()
    
    subject_id, subject_name = table_service.get_subject_id_and_name(file_bytes)
    
    # Check if the subject ID is valid
    if not subject_id:
        raise HTTPException(status_code=400, detail="El archivo no tiene un código de asignatura válido")
        
    # Check if the subject ID already exists
    if supabase_client.exists_subject_id(subject_id):
        raise HTTPException(status_code=400, detail="Ya existe una guía de aprendizaje para esa asignatura")
    
    # Process the file
    try:
        table_service.tables_to_postgres(file_bytes)
        embedding_service = EmbeddingService(subject_id)
        embedding_service.process_teaching_guide(file_bytes) 
        #Tables from pdf to PostgreSQL
        return {"message": "Guía de aprendizaje procesada correctamente", "guia_docente": subject_name, "id": subject_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/teaching-guides/")
async def get_teaching_guides():
    try:
        supabase_client = SupabaseClient()
        guides = supabase_client.get_subjects()
        return guides
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
    
    