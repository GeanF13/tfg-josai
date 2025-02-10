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
            Eres un clasificador de consultas academicas sobre una guía docente cualquiera de una asignatura de la universidad. Clasifica la consulta del usuario en una de las siguientes categorías:
            - Descripción de la categoría A: Informacion general sobre la guía docente de la asignatura, excluyendo actividades en cada evaluación y cálculos de notas.
            - Descripción de la categoría BP: Pregunta sobre evaluación progresiva (incluyendo cálculos de notas).
            - Descripción de la categoría BG: Pregunta sobre evaluación global (incluyendo cálculos de notas).
            - Descripción de la categoría BE: Pregunta sobre evaluación extraordinaria (incluyendo cálculos de notas).
            - Descripción de la categoría BT: Preguntas sobre actividades de todas las evaluaciones (incluyendo calculos de notas).
            - Descripción de la categoría C: Preguntas o frases que no puedas entender o resolver o no esten en el contexto de la guía docente como \"Qué tiempo hace?\".
            
            Aquí tienes unos ejemplos de clasificación:
            - Pregunta del usuario: Cómo se llama el profesor de la asignatura?
            - Categoria: A
            
            - Pregunta del usuario: En evaluacion progresiva, si tengo en el primer parcial un 5, en el segundo parcial un 4, en la primera practica un 5, en la segunda practica un 4, cuanto necesitaria sacar en el examen final ?
            - Categoria: BP
            
            - Pregunta del usuario: Que actividades tengo que hacer si voy por evaluacion global?
            - Categoria: BG
            
            - Pregunta del usuario: Dime todas las actividades de todas las evaluaciones
            - Categoria: BT
            
            - Pregunta del usuario: Cuanto tiempo hace hoy?
            - Categoria: C

            Devuelve solo la categoría de la siguiente pregunta del usuario.

            Pregunta del usuario: {input}
            """
        )
        
    def classify_query(self, user_query: str) -> str:
        prompt = self.classification_prompt.invoke({"input": user_query})
        print("EL PROMPT ES: " )
        print(prompt)
        response = self.llm.with_structured_output(QueryClassification).invoke(prompt)
        print(response)
        return response.model_dump().get("category")