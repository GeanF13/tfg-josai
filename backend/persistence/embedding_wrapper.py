from langchain.embeddings import OllamaEmbeddings
import numpy as np

class EmbeddingFunctionWrapper:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
    
    def __call__(self, input):
        if isinstance(input, str):
            embedding = self.embedding_model.embed_query(input)
        else:
            embedding = self.embedding_model.embed_documents(input)

        # Convertimos la lista en un numpy array antes de retornarlo
        return np.array(embedding, dtype=np.float32)