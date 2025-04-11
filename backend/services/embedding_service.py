from services.pdf_processor import PDFProcessor
from services.faq_processor import FAQProcessor
from persistence.chromadb_client import ChromaDBClient
from langchain_core.documents import Document
class EmbeddingService:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.chromadb_client = ChromaDBClient()
        self.pdf_processor = PDFProcessor(collection_name)
        self.faq_processor = FAQProcessor()

    def process_teaching_guide(self, file_bytes: bytes):
        teaching_guide_chunks = self.pdf_processor.process_pdf_from_bytes(file_bytes)
        self.__chunks_to_chroma(teaching_guide_chunks)

    def process_faq(self, file_bytes: bytes):
        faq_chunks = self.faq_processor.process_pdf_from_bytes(file_bytes)
        self.__chunks_to_chroma(faq_chunks)

    def __get_last_chunk_number(self) -> int:
        """
        Consulta la colección para obtener el número del último chunk.
        Se asume que los IDs tienen el formato "chunk_<n>".
        Retorna -1 si no se encuentran chunks.
        """
        vstore = self.chromadb_client.create_collection(self.collection_name)
        result = vstore.get(include=[])
        # El resultado generalmente viene en una lista anidada: [["chunk_0", "chunk_1", ...]]
        ids_list = result.get("ids", [[]])
        last_number = -1
        if ids_list and ids_list[0]:
            for doc_id in ids_list[0]:
                if doc_id.startswith("chunk_"):
                    try:
                        n = int(doc_id.split("_")[1])
                        if n > last_number:
                            last_number = n
                    except ValueError:
                        continue
        return last_number

    def __chunks_to_chroma(self, chunks: list[Document]):
        try:
            vstore = self.chromadb_client.create_collection(self.collection_name)
            # Obtenemos el último número de chunk asignado en la colección
            last_index = self.__get_last_chunk_number()
            start_index = last_index + 1  # Si no hay chunks, last_index es -1 y se empieza en 0
            for chunk in chunks:
                chunk_id = f"chunk_{start_index}"
                vstore.add_documents(
                    documents=[chunk],
                    ids=[chunk_id]
                )
                start_index += 1
        except Exception as e:
            raise Exception(f"Error añadiendo chunks a ChromaDB: {str(e)}")