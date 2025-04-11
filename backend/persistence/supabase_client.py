import os
from supabase import create_client, Client

from dotenv import load_dotenv
load_dotenv()  # Esto carga las variables de entorno desde un archivo .env


class SupabaseClient:
    supabase_url: str = os.getenv('SUPABASE_URL')
    supabase_key: str = os.getenv('SUPABASE_KEY')
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    def get_subject_id(self, subject_name):
        response = self.supabase.table('Subject').select('id').eq('name', subject_name).execute()
        return response.data
    
    def get_subjects(self):
        response = self.supabase.table('Subject').select('*').execute()
        return response.data
    
    def get_subject_name_by_id(self, subject_id):
        response = self.supabase.table('Subject').select('name').eq('id', subject_id).execute()
        return response.data[0]['name']
    
    def add_subject(self, subject_id, subject_name):
        self.supabase.table('Subject').insert([{'id': subject_id, 'name': subject_name}]).execute()
    
    def exists_subject_id(self, subject_id) -> bool:
        response = self.supabase.table('Subject').select('id').eq('id', subject_id).execute()
        return bool(response.data)  
    
    def get_activities_by_subject_id_and_assessment(self, subject_id, assessment_type):
        response = self.supabase.table('Activity').select('*').eq('subject_id', subject_id).eq('assessment_type', assessment_type).execute()
        return response.data
    
    def add_activity(self, assessment_type, modality, name, percentage, passing_grade, date, subject_id):
        self.supabase.table('Activity').insert([{'assessment_type': assessment_type, 'modality': modality, 'name': name, 'percentage': percentage, 'passing_grade': passing_grade, 'date': date, 'subject_id': subject_id}]).execute()
    
    def delete_activity_by_subject_id(self, subject_id):
        self.supabase.table('Activity').delete().eq('subject_id', subject_id).execute()
    
    def delete_subject(self, subject_id):
        self.supabase.table('Subject').delete().eq('id', subject_id).execute()
        
    def insert_assessment_criteria(self, criteria, subject_id):
        self.supabase.table('Subject').update({'assessment_criteria': criteria}).eq('id', subject_id).execute()

    def get_assessment_criteria_by_subject_id(self, subject_id):
        response = self.supabase.table('Subject').select('assessment_criteria').eq('id', subject_id).execute()
        return response.data[0]['assessment_criteria'] if response.data else None