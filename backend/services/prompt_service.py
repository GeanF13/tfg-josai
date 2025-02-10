from langchain.embeddings import OllamaEmbeddings
from persistence.supabase_client import SupabaseClient
from persistence.chromadb_client import ChromaDBClient
from langchain_ollama import ChatOllama
from services.utils import from_activities_list_to_string


class PromptService():
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.supabase_client = SupabaseClient()
        self.llm = ChatOllama(
            model = "llama3.2",
            temperature = 0
        )
        self.chromadb_client = ChromaDBClient()
    def query_type_a(self, subject_id, user_query):

        try:
            collection = self.chromadb_client.get_collection(subject_id)
            
            docs = collection.query(query_texts=[user_query], n_results=3)['documents']
            
            if not docs:
                return "No se encontraron resultados"
            
            formatted_docs = "\n\n".join(docs[0])
            
            prompt = f"""
            Eres un asistente que responde preguntas sobre la guía docente de una materia.
            Basándote en la siguiente información, responde la pregunta de manera clara y concisa.

            Información relevante:
            {formatted_docs}

            Pregunta del usuario:
            {user_query}
            """
            
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            raise Exception(f"Error en query_type_a: {str(e)}")
    
    def query_type_b(self, subcategory, subject_id, user_query):
        match subcategory:
            case "P":
                activities = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion progresiva")
                data_extra = from_activities_list_to_string(activities, "evaluación progresiva")
            case "G":
                activities = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion global")
                data_extra = from_activities_list_to_string(activities, "evaluación global")
            case "E":
                activities = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion extraordinaria")
                data_extra = from_activities_list_to_string(activities, "evaluación extraordinaria")
            case "T":
                activities_p = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion progresiva")
                activities_g = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion global")
                activities_e = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion extraordinaria")
                data_extra = from_activities_list_to_string(activities_p, "evaluación progresiva")
                data_extra += from_activities_list_to_string(activities_g, "evaluación global")
                data_extra += from_activities_list_to_string(activities_e, "evaluación extraordinaria")
            case _:
                data_extra = None
        if data_extra is None:
            raise ValueError("No se ha podido clasificar la pregunta.")
        
        try:
            collection = self.chromadb_client.get_collection(subject_id)
            
            docs = collection.query(query_texts=[user_query], n_results=3)['documents']
            
            if not docs:
                return "No se encontraron resultados"
            
            formatted_docs = "\n\n".join(docs[0])
            
            prompt = f"""
            Eres un asistente que ayuda a los usuarios a encontrar información sobre la guia docente de una materia y calcula notas con ayuda de datos extras.
            
            Aqui hay alguna data extra que te puedes ayudar a responder la siguiente pregunta o a calcular lo que necesites: {data_extra}
            
            La escala de notas es de 0 a 10, debes tener en cuenta que la nota minima para aprobar la materia es 5 y que las actividades tienen un peso y nota minima diferente.
            
            Pregunta del usuario:
            {user_query}
            """
            
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            raise Exception(f"Error en query_type_b: {str(e)}")