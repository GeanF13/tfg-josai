from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import re
from io import BytesIO
import tempfile
from persistence.supabase_client import SupabaseClient
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
import os
from textwrap import dedent

_CODE_FENCE_RE = re.compile(
    r"""
    ^\s*```[\w+-]*\s*        # apertura  ``` o ```markdown, ```json, etc.
    \n?                      # salto opcional
    (?P<contenido>.*?)       # todo lo de dentro (no codicioso)
    \n?\s*```?\s*$           # cierre  ``` o ```
    """,
    re.DOTALL | re.VERBOSE,
)

class PDFProcessor:
    def __init__(self, subject_id: str):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=1000,
            length_function=len
        )
        self.subject_id = subject_id
        self.supabase_client = SupabaseClient()
        self.llm = ChatOllama(
            model = "deepseek-r1:14b",
            temperature = 0
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
        
            self.__assessment_criteria_process(combined_text)
            
            chunks = self.text_splitter.split_text(combined_text)
            documents = [Document(page_content=chunk, metadata={"document_type": "teaching_guide"}) for chunk in chunks]
                        
            return documents
        except Exception as e:
            raise Exception(f"Error procesando el archivo PDF: {str(e)}")

    def __assessment_criteria_process(self, text):
        section_keyword = "criterios de evaluación"
        
        pattern = re.compile(
            rf"(?si)(?P<section>\d+\.\d+\.*\s+{re.escape(section_keyword)}.*)",
            re.DOTALL
        )
        
        match = pattern.search(text)
        if match:
            criterial_section = match.group("section").strip()
        else:
            raise Exception(f"No se encontró la sección '{section_keyword}' en el texto.")
        
        try:

            system_message = f"""Extrae el texto completo de la sección llamada "criterios de evaluación".
            Incluye todas las subsecciones y contenido hasta que comience la siguiente sección principal.
            NO incluyas el título de la sección ni ningún apunte o comentario adicional.
            **No envuelvas la respuesta en fences de código (` ``` `) ni indiques el lenguaje.**
            Devuelve SOLO Markdown plano.
            
            Documento:
            {criterial_section}
            """
            
            response = self.llm.invoke(system_message).content
            response_clean = self.__strip_code_fences(response)
            
            if response_clean:
                self.supabase_client.insert_assessment_criteria(response, self.subject_id)
            else:
                raise Exception("No se obtuvo respuesta del modelo para los criterios de evaluación.")
        except Exception as e:
            raise Exception(f"Error procesando los criterios de evaluación: {str(e)}")
        
    def __strip_code_fences(self, text):
        """
        Si el string está envuelto en un bloque de código, lo quita.
        Además elimina cualquier fence suelto que pueda quedar.
        """
        text = text.strip()

        # 1) bloque completo (apertura-cierre)
        m = _CODE_FENCE_RE.match(text)
        if m:
            text = m.group("contenido")

        # 2) por si quedaran líneas ``` desperdigadas
        text = re.sub(r"^\s*```[\w+-]*\s*$", "", text, flags=re.MULTILINE)

        return dedent(text).strip()
    
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
    
    
    