from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from models.query_classification import QueryClassification

class QueryClassifierService:
    def __init__(self):
        self.llm = ChatOllama(
            model = "llama3.2",
            temperature = 0
        )
        self.classification_prompt = ChatPromptTemplate.from_template(
            """
            Clasifica la pregunta del usuario en una de las siguientes categorías:
            - A: Pregunta general sobre la guía docente (excluyendo cálculos y actividades de evaluación).
            - BP: Pregunta sobre evaluación progresiva (incluyendo cálculos de notas).
            - BG: Pregunta sobre evaluación global (incluyendo cálculos de notas).
            - BE: Pregunta sobre evaluación extraordinaria (incluyendo cálculos de notas).
            - BT: Pregunta sobre todas las evaluaciones.
            - C: Preguntas o frases que no puedas entender o resolver o no esten en el contexto de la guía docente como \"hola\".
            
            Aquí tienes unos ejemplos:
            - Usuario: En evaluacion progresiva, si tengo en el primer parcial un 5, en el segundo parcial un 4, en la primera practica un 5, en la segunda practica un 4, cuanto necesitaria sacar en el examen final ?
            - Sistema: BP
            
            - Usuario: Que actividades tengo que hacer si voy por evaluacion global?
            - Sistema: BG
            
            - Usuario: Dime todas las actividades de todas las evaluaciones
            - Sistema: BT

            Devuelve solo la categoría.

            Pregunta del usuario: {input}
            """
        )
        
    def classify_query(self, user_query: str) -> str:
        prompt = self.classification_prompt.invoke({"input": user_query})
        response = self.llm.with_structured_output(QueryClassification).invoke(prompt)
        return response.model_dump().get("category")