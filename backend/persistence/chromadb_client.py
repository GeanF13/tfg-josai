import chromadb
import os
from langchain.embeddings import OllamaEmbeddings
from dotenv import load_dotenv
from persistence.embedding_wrapper import EmbeddingFunctionWrapper

load_dotenv()

class ChromaDBClient:
    client = chromadb.HttpClient(
        host = os.getenv('CHROMADB_HOST'),
        port = int(os.getenv('CHROMADB_PORT'))
        )
        
    def create_collection(self, collection_name: str):
        """

        Args:
            collection_name (str): Nombre de la colección

        Returns:
           Collection: Objeto de la colección creada 
        """
        try:
            ollama_embeddings = OllamaEmbeddings(model="nomic-embed-text")
            embedding_function = EmbeddingFunctionWrapper(ollama_embeddings)
            
            return self.client.create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
        except Exception as e:
            raise Exception(f"Error creando la collección: {e}")
        
    def get_collection(self, collection_name: str):
        """

        Args:
            collection_name (str): Nombre de la colección

        Returns:
            Collection: Objeto de la colección
        """
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            raise Exception(f"Error obteniendo la collección: {e}")
    
    
        
    
    
