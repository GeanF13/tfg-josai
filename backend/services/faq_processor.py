from langchain_core.documents import Document
from langchain.document_loaders import PyPDFLoader
import tempfile
import re

class FAQProcessor:
    def __init__(self):
        pass
    
    def process_pdf_from_bytes(self, file_bytes:bytes):
        if not file_bytes:
            raise Exception("Archivo vacío")
        
        try:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
                temp_pdf.write(file_bytes)
                temp_pdf.flush()  # Asegura que los datos estén escritos

                pdf_loader = PyPDFLoader(temp_pdf.name)  # Usa la ruta temporal
                pdf_text = pdf_loader.load()
        
            pages = [{'page_number': i+1, 'content': page_text.page_content} for i, page_text in enumerate(pdf_text)]
        
            normalized_pages = [{'page_number': page['page_number'], 'content': self.__normalize_text(page['content'])} for page in pages]
            
            combined_text = self.__combine_text(normalized_pages)
            chunks = self.split_faq_text(combined_text)
            
            documents = [Document(page_content=chunk, metadata={"document_type": "faq"}) for chunk in chunks]
            return documents
        except Exception as e:
            raise Exception(f"Error procesando el archivo PDF: {str(e)}")
        
    def split_faq_text(self, text: str) -> list:
        """
        Separa el texto de FAQs en chunks, cada uno conteniendo un par de Q&A completo.
        Se asume que el formato del texto es:
        
        Pregunta: ...
        Respuesta: ...
        
        Pregunta: ...
        Respuesta: ...
        """
        
        text = self.__normalize_text(text)
        
        pattern = re.compile(r"Pregunta:\s*(.*?)\s*Respuesta:\s*(.*?)(?=Pregunta:|$)", re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(text)
        chunks = []
        
        for question, answer in matches:
            if question.strip() and answer.strip():
                normalized_question = self.__normalize_text(question)
                normalized_answer = self.__normalize_text(answer)
                
                chunk = f"Pregunta: {normalized_question}\nRespuesta: {normalized_answer}"
                chunks.append(chunk)
        return chunks
                
    def __normalize_text(self, text):
        """
        Normalizes the text by converting it to lowercase and removing extra spaces.
        """
        text = text.lower().strip()
        text = " ".join(text.split())
        return text
    
    def __combine_text(self, pages):
        """
        Combines the text from all pages into a single string.
        """
        return "\n".join(page['content'] for page in pages)

    
    