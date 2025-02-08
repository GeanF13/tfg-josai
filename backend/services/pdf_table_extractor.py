import re
import pdfplumber
from unidecode import unidecode
from io import BytesIO


class PDFTableExtractor:
    def extract_tables(self, file_bytes: bytes):
        """Summary

        Args:
            file_bytes (bytes): PDF file in bytes

        Returns:
            list: List of tables extracted from the PDF
        """
        
        final_tables = []
        continuous_assessment_header = ['sem', 'descripcion', 'modalidad', 'tipo', 'duracion', 'peso en la nota',
                                     'nota minima', 'competencias evaluadas']
        final_assessment_header = ['sem', 'descripcion', 'modalidad', 'tipo', 'duracion', 'peso en la nota', 'nota minima',
                               'competencias evaluadas']
        extraordinary_assessment_header = ['descripcion', 'modalidad', 'tipo', 'duracion', 'peso en la nota', 'nota minima',
                                       'competencias evaluadas']
        
        pdf_stream = BytesIO(file_bytes)
        with pdfplumber.open(pdf_stream) as pdf:
            for page_number, page in enumerate(pdf.pages, start = 1):
                tables = page.extract_tables()
                for table_number, table in enumerate(tables, start=1):
                    cleaned_table = self.__clean_table(table)
                    if not cleaned_table:
                        continue
                    if page_number == 1 and table_number == 1:
                        final_tables.append(cleaned_table)
                    else:
                        if len(final_tables) == 1 and (cleaned_table[0] == continuous_assessment_header):
                            final_tables.append(cleaned_table)
                            continue
                        if len(final_tables) == 2 and (cleaned_table[0] != final_assessment_header):
                            final_table = self.__concat_two_tables(final_tables[1], cleaned_table)
                            final_tables[1] = final_table
                            continue
                        if len(final_tables) == 2 and (cleaned_table[0] == final_assessment_header):
                            final_tables.append(cleaned_table)
                            continue
                        if len(final_tables) == 3 and (cleaned_table[0] != extraordinary_assessment_header):
                            final_table = self.__concat_two_tables(final_tables[2], cleaned_table)
                            final_tables[2] = final_table
                            continue
                        if len(final_tables) == 3 and (cleaned_table[0] == extraordinary_assessment_header):
                            final_tables.append(cleaned_table)
                            continue
                        if len(final_tables) == 4 and (cleaned_table[0] != extraordinary_assessment_header) and len(cleaned_table[0]) == 7:
                            final_table = self.__concat_two_tables(final_tables[3], cleaned_table)
                            final_tables[3] = final_table
                            continue
                    continue
            return final_tables
    
    def __concat_two_tables(self, table1, table2):
        """Summary

        Args:
            table1 (list): First table to concatenate
            table2 (list): Second table to concatenate

        Returns:
            list: Concatenated table
        """
        
        if not table1:
            return table2
        if not table2:
            return table1
        
        if len(table1[0]) != len(table2[0]):
            raise ValueError(f"Tables have different number of columns, table1: {len(table1[0])}, table2: {len(table2[0])}")
        
        combined_table = table1 + table2
        return combined_table
    
    def __clean_table(self, table):
        """Summary

        Args:
            table (list): Table to clean

        Returns:
            list: Cleaned table
        """
        
        cleaned_table = []
        for row in table:
            cleaned_row = []
            for cell in row:
                if isinstance(cell, str):
                    cell = re.sub(r'\(?\bRA\d+\)?,?', '', cell)
                    cell = re.sub(r'\[.*?\]\s*', '', cell)
                    cell = cell.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
                    cell = cell.replace('.', '')
                    cell = cell.replace('%', '')
                    cell = re.sub(r'[\*+]', ' ', cell)
                    cell = unidecode(cell)
                    cell = cell.lower()
                    cell = re.sub(r'\s+', ' ', cell)
                cleaned_row.append(cell)
            cleaned_table.append(cleaned_row)
        return cleaned_table
                        