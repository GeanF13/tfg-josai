import pdfplumber
import re
from unidecode import unidecode
import pandas as pd
from services.pdf_table_extractor import PDFTableExtractor
from persistence.supabase_client import SupabaseClient
from services.utils import extract_number

class TablesService:
    def __init__(self):
        self.supabase = SupabaseClient()
        self.extractor = PDFTableExtractor()
    
    def tables_to_postgres(self, file_bytes: bytes):
        tables = self.extractor.extract_tables(file_bytes)
        
        tables_df = self.__tables_to_df(tables)
        subject_name = self.__extract_subject_name(tables_df[0].iloc[0, 0])
        subject_id = self.__extract_subject_id(tables_df[0].iloc[0, 0])
        
        try:
            self.supabase.add_subject(subject_id, subject_name)
            for i in range(len(tables_df[1])):
                row = tables_df[1].iloc[i]
                self.supabase.add_activity("evaluacion progresiva", row["modalidad"], row["descripcion"], int(row["peso en la nota"]), extract_number(row["nota minima"]), int(row["sem"]), subject_id)
            for i in range(len(tables_df[2])):
                row = tables_df[2].iloc[i]
                self.supabase.add_activity("evaluacion global", row["modalidad"], row["descripcion"], int(row["peso en la nota"]), extract_number(row["nota minima"]), int(row["sem"]), subject_id)
            for i in range(len(tables_df[3])):
                row = tables_df[3].iloc[i]
                self.supabase.add_activity("evaluacion extraordinaria", row["modalidad"], row["descripcion"], int(row["peso en la nota"]), extract_number(row["nota minima"]), 0, subject_id)
        except Exception as e:
            self.supabase.delete_subject(subject_id)
            self.supabase.delete_activity_by_subject_id(subject_id)
            raise Exception(f"Error adding tables to Postgres: {str(e)}")
    
    def get_subject_id_and_name(self, file_bytes: bytes):
        tables = self.extractor.extract_tables(file_bytes)
        print("Tablas extraídas:", tables)
        tables_df = self.__tables_to_df(tables)
        print("DataFrames generados:", tables_df)
        
        if not tables_df or not tables_df[0].shape[0]:  # Si la lista está vacía o el DataFrame está vacío
            raise ValueError("❌ No se encontraron tablas válidas en el PDF.")
    
        subject_id = self.__extract_subject_id(tables_df[0].iloc[0, 0])
        subject_name = self.__extract_subject_name(tables_df[0].iloc[0, 0])
        return subject_id, subject_name
        
    def __tables_to_df(self, tables):
        tables_df = []
        for table in tables:
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                tables_df.append(df)
        return tables_df
    
    def __extract_subject_name(self, text):
        parts = text.split(" - ")
        name = parts[-1]
        return name
    
    def __extract_subject_id(self, text):
        parts = text.split(" - ")
        id = parts[0]
        return id