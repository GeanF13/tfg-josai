from langchain_ollama import OllamaEmbeddings
from persistence.supabase_client import SupabaseClient
from persistence.chromadb_client import ChromaDBClient
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from services.utils import from_activities_list_to_string


class PromptService():
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.supabase_client = SupabaseClient()
        self.llm = ChatOllama(
            model = "deepseek-r1:8b",
            temperature = 0
        )
        self.chromadb_client = ChromaDBClient()
    def query_type_a(self, old_messages, recent_messages, subject_id, user_query_temp):

        try:
            vstore = self.chromadb_client.get_collection(subject_id)
            docs = vstore.similarity_search(query=user_query_temp, k=3)
            
            print("AQUI ESTA EL VSTORE")
            print(vstore)
            
            if not docs:
                return f"Error en query_type_a: {docs}"
            
            formatted_docs = "\n\n".join([doc.page_content for doc in docs])
            print(docs)
            print("AQUI ESTAN LOS DOCS FORMATTEADOS")
            print(formatted_docs)
            
            system_message = f"""
            Eres un asistente que responde preguntas sobre la guía docente de una asignatura de la universidad.
                
            Basándote en la siguiente información relevante, un historial de chat y la última pregunta del usuario, responde a esta última pregunta o cuestión del usuario de manera clara y concisa.

            Información relevante:
            {formatted_docs}
            """
            
            if old_messages:
                chat_history = old_messages + recent_messages
  
            else:
                chat_history = recent_messages
            
            prompt = [SystemMessage(content=system_message)] + chat_history
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            raise Exception(f"Error en query_type_a: {str(e)}")
    
    def query_type_b(self, subcategory, old_messages, recent_messages, subject_id, user_query_temp):
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
            vstore = self.chromadb_client.get_collection(subject_id)
            docs = vstore.similarity_search(query=user_query_temp, k=3)
            
            if not docs:
                return "No se encontraron resultados"
            
            formatted_docs = "\n\n".join(docs[0])
            
            system_message = f"""
            Eres un asistente que ayuda a los usuarios a encontrar información sobre la guia docente de una asignatura de la universidad y calcula notas con ayuda de datos extra.
                
            Es importante que sepas que la escala de notas es de 0 a 10, por lo que debes tener en cuenta que la nota minima para aprobar la asignatura es 5 y que las actividades tienen un peso y nota mínima diferente.
            
            Basándote en la siguiente información relevante, alguna data extra, un historial de chat y la última pregunta del usuario, responde a esta última pregunta o cuestión del usuario de manera clara y concisa.
                
            Información relevante:
            {formatted_docs}
                
            Data extra:
            {data_extra}
 
            """
            
            if old_messages:
                chat_history = old_messages + recent_messages
                
            else:
                chat_history = recent_messages

            prompt = [SystemMessage(content=system_message)] + chat_history
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            raise Exception(f"Error en query_type_b: {str(e)}")