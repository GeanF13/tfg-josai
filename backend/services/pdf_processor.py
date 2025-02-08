from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from io import BytesIO
import tempfile

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len
        )
    def process_pdf_from_bytes(self, file_bytes: bytes):
        if not file_bytes:
            raise Exception("Archivo vacío")
        
        try:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
                temp_pdf.write(file_bytes)
                temp_pdf.flush()  # Asegura que los datos estén escritos

                pdf_loader = PyPDFLoader(temp_pdf.name)  # Usa la ruta temporal
                pdf_text = pdf_loader.load()
        
            pages = [{'page_number': i+1, 'content': page_text.page_content} for i, page_text in enumerate(pdf_text)]
        
            cleaned_pages = self.preprocess_pages(pages)
            combined_text = self.__combine_text(cleaned_pages)
        
            return self.text_splitter.split_text(combined_text)
        except Exception as e:
            raise Exception(f"Error procesando el archivo PDF: {str(e)}")

    def preprocess_pages(self, pages):
        
        pages = [{'page_number': page['page_number'], 'content': self.__normalize_text(page['content'])} for page in pages]
        
        for i in range(1, len(pages)):
            pages[i]['content'] = self.__remove_headers(pages[i]['content'])
            
        for i in range(2, len(pages)):
            pages[i]['content'] = self.__remove_footers(pages[i]['content'])
        
        return pages
            
    def __normalize_text(self, text):
        text = text.lower()
        return text
    
    def __remove_headers(self, text):
        """Summary

        Args:
            text (str): Text to remove headers from

        Returns:
            str: Text without headers
        """
        
        words_to_remove = ["pr", "proceso", "coordinación", "coordinacion", "enseñanzas", "anx", "cl", "guía", "guia", "aprendizaje", "e.t.s", "sistemas"]
        
        lines = text.splitlines()
        max_lines = min(7, len(lines))
        
        for i in range(max_lines):
            if any(word in lines[i] for word in words_to_remove):
                lines[i] = ""
        
        text = "\n".join(line for line in lines if line.strip())
        return text
    
    def __remove_footers(self, text):
        """Summary

        Args:
            text (str): Text to remove footers from 

        Returns:
            str: Text without footers
        """
        
        lines = text.splitlines()
        total_lines = len(lines)
        
        if total_lines < 5:
            return text
        
        idx_fifth = total_lines - 5
        idx_fourth = total_lines - 4
        idx_third = total_lines - 3
        idx_second = total_lines - 2
        idx_last = total_lines - 1
        
        pattern_fifth_last_line = re.compile(r"^ga_61.._\d+$", re.IGNORECASE)
        pattern_fourth_last_line = re.compile(r"^\d+[a-z]?_\d{4}-\d{2}$", re.IGNORECASE)
        pattern_last_line = re.compile(r"^p[áa]gina\s+\d+\s+de\s+\d+$", re.IGNORECASE)
    
        removed_fifth_last_line = False
        removed_fourth_last_line = False
        removed_last_line = False
        
        if pattern_fifth_last_line.match(lines[idx_fifth]):
            lines[idx_fifth] = ""
            removed_fifth_last_line = True
            
        if pattern_fourth_last_line.match(lines[idx_fourth]):
            lines[idx_fourth] = ""
            removed_fourth_last_line = True
        
        if pattern_last_line.match(lines[idx_last]):
            lines[idx_last] = ""
            removed_last_line = True
        
        if removed_fifth_last_line and removed_fourth_last_line and removed_last_line:
            lines[idx_third] = ""
            lines[idx_second] = ""
        
        text = "\n".join(line for line in lines if line.strip())
        return text
        
    def __combine_text(self, pages):
        return "\n".join(page['content'] for page in pages)
    
    
    