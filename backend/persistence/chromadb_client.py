import chromadb
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

load_dotenv()

class ChromaDBClient:
    client = chromadb.HttpClient(
        host = os.getenv('CHROMADB_HOST'),
        port = int(os.getenv('CHROMADB_PORT'))
        )
        
    def create_collection(self, collection_name: str):
        try:
            ollama_embeddings = OllamaEmbeddings(model="nomic-embed-text")
            vector_store = Chroma(
                client = self.client,
                collection_name = collection_name,
                embedding_function = ollama_embeddings
            )
            vector_store.get
            return vector_store
        except Exception as e:
            raise Exception(f"Error creando la collección: {e}")
        
    def get_collection(self, collection_name: str):
        try:
            ollama_embeddings = OllamaEmbeddings(model="nomic-embed-text")
            vector_store = Chroma(
                client = self.client,
                collection_name = collection_name,
                embedding_function = ollama_embeddings
            )
            return vector_store
        except Exception as e:
            raise Exception(f"Error obteniendo la collección: {e}")
    
    
        
    
    
