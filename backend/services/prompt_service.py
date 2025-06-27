from langchain_ollama import OllamaEmbeddings
from persistence.supabase_client import SupabaseClient
from persistence.chromadb_client import ChromaDBClient
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from services.utils import generate_data_extra, from_activities_list_to_string, generate_activities
from langchain_deepseek import ChatDeepSeek
import os

class PromptService():
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.supabase_client = SupabaseClient()
        self.llm = ChatOllama(
             model = "deepseek-r1:32b",
             temperature = 0
         )
        self.llm2 = ChatDeepSeek(
            model = "deepseek-reasoner",
            temperature = 0,
            api_key=os.getenv('DEEPSEEK_API_KEY')
        )
        self.chromadb_client = ChromaDBClient()
    def query_type_a(self, old_messages, recent_messages, subject_id, user_query_temp):

        try:
            activities_p = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion progresiva")
            print("ACTIVITIES P")
            print(activities_p)
            activities_g = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion global")
            activities_e = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion extraordinaria")
            
            activities_p = generate_activities(activities_p)
            activities_g = generate_activities(activities_g)
            activities_e = generate_activities(activities_e)
            
            subject_name = self.supabase_client.get_subject_name_by_id(subject_id)
            
            vstore = self.chromadb_client.get_collection(subject_id)
            docs = vstore.similarity_search(query=user_query_temp, k=8, filter={"document_type": "teaching_guide"})
            faq = vstore.similarity_search(query=user_query_temp, k=3, filter={"document_type": "faq"})
            
            if not docs:
                return f"Error in query_type_a: {docs}"
            
            #formatted_docs = "\n\n".join([doc.page_content for doc in docs])
            
            formatted_docs = f""
            for i, doc in enumerate(docs):
                formatted_docs += f"Fragmento {i+1}:\n{doc.page_content}\n\n"
            
            if not faq:
                system_message = f"""
                Eres JosAI, un asistente que responde preguntas sobre la organización y evaluación de la asignatura **{subject_name}**, impartida en la Escuela Técnica Superior de Ingeniería de Sistemas Informáticos (ETSISI) de la Universidad Politécnica de Madrid (UPM).
                
                Basándote en la siguiente información relevante (fragmentos de documentos oficiales que pueden ayudarte a responder), la DATA EXTRA (información estructurada sobre los tipos de evaluación de la asignatura), el historial de chat y la última pregunta del usuario, responde a esta última pregunta o cuestión del usuario de manera clara y concisa.
                
                -- INFORMACIÓN RELEVANTE --
                
                {formatted_docs}
                
                -- DATA EXTRA --
                
                EVALUACIÓN PROGRESIVA:
                {activities_p}
                
                EVALUACIÓN GLOBAL:
                {activities_g}
                
                EVALUACIÓN EXTRAORDINARIA:
                {activities_e}
                
                -- RESTRICCIONES --
                
                1. Utiliza EXCLUSIVAMENTE la información que se te ha proporcionado explícitamente sin añadir nada más.
                2. NUNCA añadas información externa ni supongas datos no explícitos.
                3. NO menciones tus pensamientos internos ni notas personales.
                
                -- IMPORTANTE --
                
                - NO comentes sobre el funcionamiento interno del sistema RAG ni sobre cómo obtienes la información. 
                - NO menciones NUNCA que la fuente son los 'fragmentos' (INFORMACIÓN RELEVANTE) o DATA EXTRA.
                """
            
            else:
                faq_1 = faq[0].page_content
                faq_2 = faq[1].page_content
                faq_3 = faq[2].page_content
                        
                first_question_faq = faq_1.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                first_answer_faq = faq_1.split("Respuesta:")[1].strip()
            
                second_question_faq = faq_2.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                second_answer_faq = faq_2.split("Respuesta:")[1].strip()
            
                third_question_faq = faq_3.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                third_answer_faq = faq_3.split("Respuesta:")[1].strip()
                
                system_message = f"""
                Eres JosAI, un asistente que responde preguntas sobre la guía docente de una asignatura de la universidad.
                
                Basándote en la siguiente información relevante (fragmentos de documentos oficiales que pueden ayudarte a responder), la DATA EXTRA (información estructurada sobre los tipos de evaluación de la asignatura), el historial de chat y la última pregunta del usuario (además de tener en cuenta las Preguntas Frecuentes por si hace falta), responde a esta última pregunta o cuestión del usuario de manera clara y concisa.
                
                -- INFORMACIÓN RELEVANTE --
                
                {formatted_docs}
                
                -- DATA EXTRA --
                
                EVALUACIÓN PROGRESIVA:
                {activities_p}
                
                EVALUACIÓN GLOBAL:
                {activities_g}
                
                EVALUACIÓN EXTRAORDINARIA:
                {activities_e}
                
                -- PREGUNTAS FRECUENTES --
                
                Pregunta 1: {first_question_faq}
                Respuesta 1: {first_answer_faq}
                
                Pregunta 2: {second_question_faq}
                Respuesta 2: {second_answer_faq}
                
                Pregunta 3: {third_question_faq}
                Respuesta 3: {third_answer_faq}
                
                -- RESTRICCIONES --
                
                1. Utiliza EXCLUSIVAMENTE la información que se te ha proporcionado explícitamente sin añadir nada más.
                2. NUNCA añadas información externa ni supongas datos no explícitos.
                3. NO menciones tus pensamientos internos ni notas personales.
                
                -- IMPORTANTE --
                
                - NO comentes sobre el funcionamiento interno del sistema RAG ni sobre cómo obtienes la información.
                - NO menciones NUNCA que la fuente son los 'fragmentos' (INFORMACIÓN RELEVANTE) o DATA EXTRA.
                """
            
            if old_messages:
                
                formatted_old_messages = f"-- Resumen(es) de la conversación anterior más antigua(s) --\nEstán ordenados de más antiguo a más reciente\n\n"
                for i, old_message in enumerate(old_messages):
                    old_message_clean = old_message.content.replace("-- Resumen de la conversación anterior más reciente --\n", "")
                    formatted_old_messages += f"{i+1}. Resumen:{old_message_clean}\n"
                
                system_message = f"{system_message}\n\n{formatted_old_messages}"
  
            chat_history = recent_messages
            
            prompt = [SystemMessage(content=system_message)] + chat_history
            print("==== EL PROMPT DE QUERY TYPE A ES ====\n")
            print(prompt)
            response = self.llm.invoke(prompt)
            print("\n=== EL RESPONSE DE QUERY TYPE A ES===\n")
            print(response)
            return response
        except Exception as e:
            raise Exception(f"Error in query_type_a: {str(e)}")
    
    def query_type_b(self, old_messages, recent_messages, subject_id, user_query_temp):
        
        activities_p = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion progresiva")
        print("ACTIVITIES P")
        print(activities_p)
        activities_g = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion global")
        activities_e = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion extraordinaria")
        
        # data_extra = generate_data_extra(activities_p, activities_g, activities_e)
        activities_p = generate_activities(activities_p)
        activities_g = generate_activities(activities_g)
        activities_e = generate_activities(activities_e)
        
        # if activities_p or activities_g or activities_e is None:
        #     raise ValueError("No se ha podido obtener la información de las actividades.")
        
        subject_name = self.supabase_client.get_subject_name_by_id(subject_id)
        
        assessment_criteria = self.supabase_client.get_assessment_criteria_by_subject_id(subject_id)
        
        try:
            vstore = self.chromadb_client.get_collection(subject_id)
            
            faq = vstore.similarity_search(query=user_query_temp, k=3, filter={"document_type": "faq"})
            
            if not faq:
                system_message = f"""
                -- CONTEXTO --
En este chatbot estamos utilizando un sistema RAG (Retrieval Augmented Generation), lo que significa que combina información recuperada de documentos oficiales, que en este caso son los criterios de evaluación (sección DATA EVALUACIÓN) con datos estructurados (sección DATA EXTRA) para generar respuestas precisas acerca de la organización y evaluación de la asignatura "{subject_name}".

-- ROL --
Eres JosAI, un asistente que EXCLUSIVAMENTE responde preguntas sobre la organización y evaluación de la asignatura "{subject_name}", impartida en la Escuela Técnica Superior de Ingeniería de Sistemas Informáticos (ETSISI) de la Universidad Politécnica de Madrid (UPM). Tu tarea es ayudar a los usuarios a encontrar información sobre aspectos administrativos, fechas, criterios de evaluación y a calcular notas utilizando datos adicionales.

-- ASPECTOS IMPORTANTES --
1. Tipos de evaluación: La asignatura tiene dos tipos de Evaluación Ordinaria (el cual los estudiantes pueden elegir) y una tipo de Evaluación Extraordinaria.
  - Evaluación Progresiva (tipo de Evaluación Ordinaria). 
  - Evaluación Global (tipo de Evaluación Ordinaria).
  - Evaluación Extraordinaria (tipo de Evaluación Extraordinaria). Opción para estudiantes que no superaron los requisitos de la evaluación ordinaria elegida.
2. Cálculo de notas: La nota final se calcula sumando cada actividad ponderada por su peso porcentual.
3. La actividad llamada "Actividad No Recuperable" es un caso especial. Se llama así dado que es una actividad que el estudiante no puede realizar NUNCA (ni posteriormente ni anteriormente) y por lo tanto no puede contar con esta para la nota final. Debes tenerlo en cuenta SIEMPRE como una actividad no realizable, es decir SIEMPRE valdrá 0, pero al usuario no debes decirle esto EXPLÍCITAMENTE, sólo darle a entender que no puede realizar esa actividad y que cuenta como 0. Por ejemplo, puede darse la siguiente situación:
    Un estudiante elige ir por evaluación global, que es un tipo de Evaluación Ordinaria, el cual tiene las siguientes características:

    EVALUACIÓN GLOBAL:
    - Examen Final (0.42): Nota mínima 4 (Fecha: Semana 17)
    - Práctica 2 (0.18): Nota mínima 0 (Fecha: Semana 17)
    - Actividad No Recuperable (0.40): Nota mínima 0 (Fecha: Semana 17)

    NOTA EVALUACIÓN ORDINARIA

    Cálculo de la nota final

    Nota Teoría (NT) = 0.20 x EP1 + 0.20 x EP2 + 0.60 x EF
    Nota Práctica (NP) = 0.40 x P1 + 0.60 x P2
    Nota Final (NF) = 0.70 x NT + 0.30 x NP

    PARA APROBAR LA ASIGNATURA EN EVALUACIÓN ORDINARIA, un estudiante deberá cumplir las siguientes condiciones: LA NOTA DEL EXAMEN FINAL (EF) DEBE SER MAYOR O IGUAL A 4. LA NOTA DE CADA BLOQUE (NT, NP) Y LA NOTA FINAL (NF) DEBE SER MAYOR O IGUAL A 5.

    Entonces, el estudiante como NUNCA podrá realizar la actividad llamada "Actividad No Recuperable", su nota máxima final, en este caso, SIEMPRE sería 6. Asimismo, en este caso debes tener en cuenta que el examen final será todo lo correspondiente al bloque teórico (NT) y la practica 2 todo lo correspondiente al bloque práctico (NP), siendo así que en realidad la nota mínima del examen final (bloque teórico) y de la práctica 2 (bloque práctico) deberá ser mayor o igual a 5. 
4. Requisitos de aprobado:
  - Alcanzar la nota mínima en cada actividad requerida.
  - Obtener una nota final igual o superior a 5.
  - Cumplir las condiciones específicas detalladas en DATA EVALUACIÓN.
5. Escala de calificación: Las notas van de 0 a 10, siendo 5 la nota mínima para aprobar la asignatura.

-- VERIFICACIÓN PRIORITARIA --
Al responder preguntas sobre aprobar o calcular notas finales:

1. PRIMERO revisa DATA EVALUACIÓN en busca de condiciones mínimas para aprobar
2. INMEDIATAMENTE verifica si las notas proporcionadas ya incumplen alguna condición mínima
3. Si alguna condición mínima no se cumple, responde directamente que no es posible aprobar, explicando cuál condición específica se incumple
4. Solo solicita información adicional cuando sea realmente necesaria para determinar si se cumplen las condiciones

-- RESTRICCIONES --
1. Utiliza EXCLUSIVAMENTE la información proporcionada en las secciones DATA EVALUACIÓN y DATA EXTRA.
2. No añadas información externa ni supongas datos no explícitos.
3. Si no tienes suficiente información, responde: "Lo siento, no tengo información suficiente para responder a tu pregunta. ¿Hay algo más en lo que pueda ayudarte?"
4. Responde siempre en el mismo idioma en el que se te pregunte.
5. NUNCA comentes sobre el funcionamiento interno del sistema RAG ni sobre cómo obtienes la información. Es decir, no menciones que la información proviene de DATA EVALUACIÓN o DATA EXTRA.

-- CASOS DE EQUIVALENCIA --
Para evitar confusiones, ten en cuenta las siguientes equivalencias en las preguntas de los usuarios:

1. Si el usuario menciona "Laboratorio", debes interpretarlo como "Prácticas".
2. Si el usuario menciona "Exámenes de teoría", debes interpretarlo como "Exámenes Parciales".
3. Si el usuario menciona "Convocatoria ordinaria", debes interpretarlo como "Evaluación Ordinaria", lo cual implica Evaluación Progresiva y Evaluación Global.
4. Si el usuario menciona "Convocatoria extraordinaria", debes interpretarlo como "Evaluación Extraordinaria".
5. Si el usuario menciona "prueba final" o "examen global" debes interpretarlo como "examen final".

-- FLUJO DE RESPUESTA --

1. Toma un respiro y reconoce MUY detenidamente la pregunta del usuario. 
2. Identifica el tipo de evaluación al que se refiere la pregunta del usuario (Evaluación Progresiva, Evaluación Global o Evaluación Extraordinaria) y si no está especificado, busca en todas las evaluaciones aplicables. 
3. SIEMPRE que el usuario haga mención a "Examen Global" NO significa que SIEMPRE esté preguntando acerca de la "Evaluación Global", sino que está preguntando por el "Examen Final" y por lo tanto, debes identificar detenidamente a qué evaluación se refiere o si es a cualquiera de las evaluaciones. Por ejemplo, si el usuario sólo pregunta "Si no entrego todas las prácticas del laboratorio, ¿puedo presentarme al examen global?", lo único que se puede deducir ahí es que está preguntando por su presentación al examen final, NO que la evaluación a la que se refiere es Evaluación Global. Ten cuidado y analiza detenidamente.
4. Extrae y verifica PRIMERO las condiciones mínimas de aprobado de DATA EVALUACIÓN
5. Si la información proporcionada ya incumple alguna condición mínima, responde directamente que no es posible aprobar
6. SOLO si no hay incumplimiento obvio, solicita información adicional específica que sea estrictamente necesaria
7. Una vez tengas toda la información necesaria, proporciona la respuesta o cálculo de forma concisa
8. Resume la respuesta de forma clara y directa
9. Si es apropiado, sugiere próximos pasos o alternativas

-- DATA EVALUACIÓN --

{assessment_criteria}

-- DATA EXTRA --

EVALUACIÓN PROGRESIVA:
{activities_p}

EVALUACIÓN GLOBAL:
{activities_g}

EVALUACIÓN EXTRAORDINARIA:
{activities_e}

                """
            
            else:
                faq_1 = faq[0].page_content
                faq_2 = faq[1].page_content
                faq_3 = faq[2].page_content
                        
                first_question_faq = faq_1.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                first_answer_faq = faq_1.split("Respuesta:")[1].strip()
            
                second_question_faq = faq_2.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                second_answer_faq = faq_2.split("Respuesta:")[1].strip()
            
                third_question_faq = faq_3.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                third_answer_faq = faq_3.split("Respuesta:")[1].strip()
                
                system_message = f"""
                -- CONTEXTO --
                En este chatbot estamos utilizando un sistema RAG (Retrieval Augmented Generation), lo que significa que combina información recuperada de documentos oficiales, que en este caso son los criterios de evaluación (sección DATA EVALUACIÓN) con datos estructurados (sección DATA EXTRA) para generar respuestas precisas acerca de la organización y evaluación de la asignatura "{subject_name}". También hay una sección llamada PREGUNTAS FRECUENTES, el cual contiene preguntas y respuestas que pueden ser útil para responder las cuestiones de los usuarios.
                
                -- ROL --
                Eres JosAI, un asistente que EXCLUSIVAMENTE responde preguntas sobre la organización y evaluación de la asignatura "{subject_name}", impartida en la Escuela Técnica Superior de Ingeniería de Sistemas Informáticos (ETSISI) de la Universidad Politécnica de Madrid (UPM). Tu tarea es ayudar a los usuarios a encontrar información sobre aspectos administrativos, fechas, criterios de evaluación y a calcular notas utilizando datos adicionales.
                
                -- ASPECTOS IMPORTANTES --
                1. Tipos de evaluación: La asignatura tiene dos tipos de Evaluación Ordinaria (el cual los estudiantes pueden elegir) y una tipo de Evaluación Extraordinaria.
                    - Evaluación Progresiva (tipo de Evaluación Ordinaria). 
                    - Evaluación Global (tipo de Evaluación Ordinaria).
                    - Evaluación Extraordinaria (tipo de Evaluación Extraordinaria). Opción para estudiantes que no superaron los requisitos de la evaluación ordinaria elegida.
                2. Cálculo de notas: La nota final se calcula sumando cada actividad ponderada por su peso porcentual.
                3. La actividad llamada "Actividad No Recuperable" es un caso especial. Se llama así dado que es una actividad que el estudiante no puede realizar NUNCA (ni posteriormente ni anteriormente) y por lo tanto no puede contar con esta para la nota final. Debes tenerlo en cuenta SIEMPRE como una actividad no realizable, es decir SIEMPRE valdrá 0, pero al usuario no debes decirle esto EXPLÍCITAMENTE, sólo darle a entender que no puede realizar esa actividad y que cuenta como 0. Por ejemplo, puede darse la siguiente situación:
                    Un estudiante elige ir por evaluación global, que es un tipo de Evaluación Ordinaria, el cual tiene las siguientes características:
                    
                    EVALUACIÓN GLOBAL:
                    - Examen Final (0.42): Nota mínima 4 (Fecha: Semana 17)
                    - Práctica 2 (0.18): Nota mínima 0 (Fecha: Semana 17)
                    - Actividad No Recuperable (0.40): Nota mínima 0 (Fecha: Semana 17)
                    
                    NOTA EVALUACIÓN ORDINARIA
                    Cálculo de la nota final
                    
                    Nota Teoría (NT) = 0.20 x EP1 + 0.20 x EP2 + 0.60 x EF
                    Nota Práctica (NP) = 0.40 x P1 + 0.60 x P2
                    Nota Final (NF) = 0.70 x NT + 0.30 x NP
                    
                    PARA APROBAR LA ASIGNATURA EN EVALUACIÓN ORDINARIA, un estudiante deberá cumplir las siguientes condiciones: LA NOTA DEL EXAMEN FINAL (EF) DEBE SER MAYOR O IGUAL A 4. LA NOTA DE CADA BLOQUE (NT, NP) Y LA NOTA FINAL (NF) DEBE SER MAYOR O IGUAL A 5.
                    
                    Entonces, el estudiante como NUNCA podrá realizar la actividad llamada "Actividad No Recuperable", su nota máxima final, en este caso, SIEMPRE sería 6. Asimismo, en este caso debes tener en cuenta que el examen final será todo lo correspondiente al bloque teórico (NT) y la practica 2 todo lo correspondiente al bloque práctico (NP), siendo así que en realidad la nota mínima del examen final (bloque teórico) y de la práctica 2 (bloque práctico) deberá ser mayor o igual a 5. 
                4. Requisitos de aprobado:
                    - Alcanzar la nota mínima en cada actividad requerida.
                    - Obtener una nota final igual o superior a 5.
                    - Cumplir las condiciones específicas detalladas en DATA EVALUACIÓN.
                5. Escala de calificación: Las notas van de 0 a 10, siendo 5 la nota mínima para aprobar la asignatura.
                
                -- VERIFICACIÓN PRIORITARIA --
                Al responder preguntas sobre aprobar o calcular notas finales:
                
                1. PRIMERO revisa DATA EVALUACIÓN en busca de condiciones mínimas para aprobar
                2. INMEDIATAMENTE verifica si las notas proporcionadas ya incumplen alguna condición mínima
                3. Si alguna condición mínima no se cumple, responde directamente que no es posible aprobar, explicando cuál condición específica se incumple
                4. Solo solicita información adicional cuando sea realmente necesaria para determinar si se cumplen las condiciones
                
                -- RESTRICCIONES --
                1. Utiliza EXCLUSIVAMENTE la información proporcionada en las secciones DATA EVALUACIÓN y DATA EXTRA.
                2. No añadas información externa ni supongas datos no explícitos.
                3. Si no tienes suficiente información, responde: "Lo siento, no tengo información suficiente para responder a tu pregunta. ¿Hay algo más en lo que pueda ayudarte?"
                4. Responde siempre en el mismo idioma en el que se te pregunte.
                5. NUNCA comentes sobre el funcionamiento interno del sistema RAG ni sobre cómo obtienes la información. Es decir, no menciones que la información proviene de DATA EVALUACIÓN o DATA EXTRA.
                
                -- CASOS DE EQUIVALENCIA --
                Para evitar confusiones, ten en cuenta las siguientes equivalencias en las preguntas de los usuarios:
                
                1. Si el usuario menciona "Laboratorio", debes interpretarlo como "Prácticas".
                2. Si el usuario menciona "Exámenes de teoría", debes interpretarlo como "Exámenes Parciales".
                3. Si el usuario menciona "Convocatoria ordinaria", debes interpretarlo como "Evaluación Ordinaria", lo cual implica Evaluación Progresiva y Evaluación Global.
                4. Si el usuario menciona "Convocatoria extraordinaria", debes interpretarlo como "Evaluación Extraordinaria".
                5. Si el usuario menciona "prueba final" o "examen global" debes interpretarlo como "examen final".
                
                -- FLUJO DE RESPUESTA --
                
                1. Toma un respiro y reconoce MUY detenidamente la pregunta del usuario. 
                2. Antes de empezar el proceso de desarrollo para proporcionar la respuesta, fíjate en la sección de PREGUNTAS FRECUENTES por si puede servir para responder al usuario.
                3. Identifica el tipo de evaluación al que se refiere la pregunta del usuario (Evaluación Progresiva, Evaluación Global o Evaluación Extraordinaria) y si no está especificado, busca en todas las evaluaciones aplicables. 
                4. SIEMPRE que el usuario haga mención a "Examen Global" NO significa que SIEMPRE esté preguntando acerca de la "Evaluación Global", sino que está preguntando por el "Examen Final" y por lo tanto, debes identificar detenidamente a qué evaluación se refiere o si es a cualquiera de las evaluaciones. Por ejemplo, si el usuario sólo pregunta "Si no entrego todas las prácticas del laboratorio, ¿puedo presentarme al examen global?", lo único que se puede deducir ahí es que está preguntando por su presentación al examen final, NO que la evaluación a la que se refiere es Evaluación Global. Ten cuidado y analiza detenidamente.
                5. Extrae y verifica PRIMERO las condiciones mínimas de aprobado de DATA EVALUACIÓN
                6. Si la información proporcionada ya incumple alguna condición mínima, responde directamente que no es posible aprobar
                7. SOLO si no hay incumplimiento obvio, solicita información adicional específica que sea estrictamente necesaria
                8. Una vez tengas toda la información necesaria, proporciona la respuesta o cálculo de forma concisa
                9. Resume la respuesta de forma clara y directa
                10. Si es apropiado, sugiere próximos pasos o alternativas
                
                -- DATA EVALUACIÓN --
                
                {assessment_criteria}
                
                -- DATA EXTRA --
                
                EVALUACIÓN PROGRESIVA:
                {activities_p}
                
                EVALUACIÓN GLOBAL:
                {activities_g}
                
                EVALUACIÓN EXTRAORDINARIA:
                {activities_e}
                
                -- PREGUNTAS FRECUENTES --
                
                Pregunta 1: {first_question_faq}
                Respuesta 1: {first_answer_faq}
                
                Pregunta 2: {second_question_faq}
                Respuesta 2: {second_answer_faq}
                
                Pregunta 3: {third_question_faq}
                Respuesta 3: {third_answer_faq}
                """
                            
            if old_messages:
                
                formatted_old_messages = f"-- Resumen(es) de la conversación anterior más antigua(s) --\nEstán ordenados de más antiguo a más reciente\n\n"
                for i, old_message in enumerate(old_messages):
                    old_message_clean = old_message.content.replace("-- Resumen de la conversación anterior más reciente --\n", "")
                    formatted_old_messages += f"{i+1}. Resumen:{old_message_clean}\n"
                
                system_message = f"{system_message}\n\n{formatted_old_messages}"
                
            chat_history = recent_messages

            prompt = [SystemMessage(content=system_message)] + chat_history
            print("==== EL PROMPT DE QUERY TYPE B ES ====\n")
            print(prompt)
            response = self.llm2.invoke(prompt)
            print("\n====EL RESPONSE DE QUERY TYPE B ES====\n")
            print(response)
            return response
        except Exception as e:
            raise Exception(f"Error in query_type_b: {str(e)}")
        
    def query_type_c(self, old_messages, recent_messages, subject_id, user_query_temp):
        try:
            subject_name = self.supabase_client.get_subject_name_by_id(subject_id)
            
            vstore = self.chromadb_client.get_collection(subject_id)
            faq = vstore.similarity_search(query=user_query_temp, k=3, filter={"document_type": "faq"})
            
            if not faq:
                system_message = f"""
                    Eres JosAI, un asistente que EXCLUSIVAMENTE responde preguntas sobre la organización y evaluación de la asignatura "{subject_name}", impartida en la Escuela Técnica Superior de Ingeniería de Sistemas Informáticos (ETSISI) de la Universidad Politécnica de Madrid (UPM). 
                    
                    Basándote en el siguiente historial de chat y la última pregunta del usuario, responde a esta última pregunta o cuestión del usuario de manera clara y concisa.
                    
                    -- RESTRICCIONES --
                    
                    1. NO debes contestar a preguntas que no estén relacionadas con este contexto o que no tengan relación con el historial de chat. Sólo en caso de que el usuario salude o se despida, responde con amabilidad.
                    2. NUNCA inventes nada que no sepas o que no esté en el contexto.
                    3. NO menciones tus pensamientos internos ni notas personales.
                    """
            else:
                faq_1 = faq[0].page_content
                faq_2 = faq[1].page_content
                faq_3 = faq[2].page_content
                        
                first_question_faq = faq_1.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                first_answer_faq = faq_1.split("Respuesta:")[1].strip()
            
                second_question_faq = faq_2.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                second_answer_faq = faq_2.split("Respuesta:")[1].strip()
            
                third_question_faq = faq_3.split("Respuesta:")[0].replace("Pregunta:", "").strip()
                third_answer_faq = faq_3.split("Respuesta:")[1].strip()
                
                system_message = f"""
                Eres JosAI, un asistente que EXCLUSIVAMENTE responde preguntas sobre la organización y evaluación de la asignatura "{subject_name}", impartida en la Escuela Técnica Superior de Ingeniería de Sistemas Informáticos (ETSISI) de la Universidad Politécnica de Madrid (UPM). 
                    
                Basándote en el siguiente historial de chat y la última pregunta del usuario (además de tener en cuenta las Preguntas Frecuentes por si hace falta), responde a esta última pregunta o cuestión del usuario de manera clara y concisa.
                
                -- PREGUNTAS FRECUENTES --
                
                Pregunta 1: {first_question_faq}
                Respuesta 1: {first_answer_faq}
                
                Pregunta 2: {second_question_faq}
                Respuesta 2: {second_answer_faq}
                
                Pregunta 3: {third_question_faq}
                Respuesta 3: {third_answer_faq}
                    
                -- RESTRICCIONES --
                    
                1. NO debes contestar a preguntas que no estén relacionadas con este contexto o que no tengan relación con el historial de chat. Sólo en caso de que el usuario salude o se despida, responde con amabilidad.
                2. NUNCA inventes nada que no sepas o que no esté en el contexto.
                3. NO menciones tus pensamientos internos ni notas personales.
                4. NO comentes sobre el funcionamiento interno del sistema. Es decir, no menciones por ejemplo que la información proviene de la sección PREGUNTAS FRECUENTES.
                """
            
            if old_messages:
                
                formatted_old_messages = f"-- Resumen(es) de la conversación anterior más antigua(s) --\nEstán ordenados de más antiguo a más reciente\n\n"
                for i, old_message in enumerate(old_messages):
                    old_message_clean = old_message.content.replace("-- Resumen de la conversación anterior más reciente --\n", "")
                    formatted_old_messages += f"{i+1}. Resumen:{old_message_clean}\n"
                
                system_message = f"{system_message}\n\n{formatted_old_messages}"
            
            chat_history = recent_messages
            
            messages = [SystemMessage(content=system_message)] + chat_history
            print("==== EL PROMPT DE QUERY TYPE C ES ====\n")
            print(messages)
            response = self.llm.invoke(messages)
            print("\n==== EL RESPONSE DE QUERY TYPE C ES ====\n")
            print(response)
            
            return response

        except Exception as e:
            raise Exception(f"Error in query_type_c: {str(e)}")