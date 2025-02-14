from services.pdf_processor import PDFProcessor
from persistence.chromadb_client import ChromaDBClient

class EmbeddingService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.chromadb_client = ChromaDBClient()
    
    def process_teaching_guide(self, file_bytes: bytes, collection_name):
        teaching_guide_chunks = self.pdf_processor.process_pdf_from_bytes(file_bytes)
        self.__chunks_to_chroma(teaching_guide_chunks, collection_name)
        
    def __chunks_to_chroma(self, chunks, collection_name):
        try:
            vstore = self.chromadb_client.create_collection(collection_name)
            for index, chunk in enumerate(chunks):
                vstore.add_documents(
                    documents = [chunk],
                    ids = [f"chunk_{index}"]
                )
        except Exception as e:
            raise Exception(f"Error añadiendo chunks a ChromaDB: {str(e)}")
        