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
        # self.llm = ChatOllama(
        #     model = "deepseek-r1:32b",
        #     temperature = 0
        # )
        self.llm = ChatDeepSeek(
            model = "deepseek-reasoner",
            temperature = 0,
            api_key=os.getenv('DEEPSEEK_API_KEY')
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
            print("EL RESPONSE DE QUERY TYPE A ES: ")
            print(response)
            return response
        except Exception as e:
            raise Exception(f"Error en query_type_a: {str(e)}")
    
    def query_type_b(self, subcategory, old_messages, recent_messages, subject_id, user_query_temp):
        # match subcategory:
        #     case "P":
        #         activities = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion progresiva")
        #         data_extra = from_activities_list_to_string(activities, "evaluación progresiva")
        #     case "G":
        #         activities = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion global")
        #         data_extra = from_activities_list_to_string(activities, "evaluación global")
        #     case "E":
        #         activities = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion extraordinaria")
        #         data_extra = from_activities_list_to_string(activities, "evaluación extraordinaria")
        #     case "T":
        #         activities_p = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion progresiva")
        #         print("ACTIVITIES P")
        #         print(activities_p)
        #         activities_g = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion global")
        #         activities_e = self.supabase_client.get_activities_by_subject_id_and_assessment(subject_id, "evaluacion extraordinaria")
        #         # data_extra = from_activities_list_to_string(activities_p, "evaluación progresiva")
        #         # data_extra += from_activities_list_to_string(activities_g, "evaluación global")
        #         # data_extra += from_activities_list_to_string(activities_e, "evaluación extraordinaria")
        #         data_extra = generate_data_extra(activities_p, activities_g, activities_e)
        #     case _:
        #         data_extra = None
        # if data_extra is None:
        #     raise ValueError("No se ha podido clasificar la pregunta.")
        
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
        
        try:
            vstore = self.chromadb_client.get_collection(subject_id)
            docs = vstore.similarity_search(query=user_query_temp, k=3)
            
            if not docs:
                return f"Error en query_type_b: {docs}"
            
            formatted_docs = "\n\n".join([doc.page_content for doc in docs])
            print(docs)
            print("AQUI ESTAN LOS DOCS FORMATTEADOS")
            print(formatted_docs)
            
            formatted_doc_1 = docs[0].page_content
            formatted_doc_2 = docs[1].page_content
            formatted_doc_3 = docs[2].page_content
            
            subject_name = self.supabase_client.get_subject_name_by_id(subject_id)
            
            system_message = f"""

-- CONTEXTO --
En este chatbot estamos utilizando un sistema RAG (Retrieval Augmented Generation), lo que significa que combina información recuperada de documentos oficiales, que en este caso son los criterios de evaluación (sección DATA EVALUACIÓN) con datos estructurados (sección DATA EXTRA) para generar respuestas precisas acerca de la organización y evaluación de la asignatura "{subject_name}".

-- ROL --
Eres un asistente que EXCLUSIVAMENTE responde preguntas sobre la organización y evaluación de la asignatura "{subject_name}", impartida en la Escuela Técnica Superior de Ingeniería de Sistemas Informáticos (ETSISI) de la Universidad Politécnica de Madrid (UPM). Tu tarea es ayudar a los usuarios a encontrar información sobre aspectos administrativos, fechas, criterios de evaluación y a calcular notas utilizando datos adicionales.

-- ASPECTOS IMPORTANTES --
1. Tipos de evaluación: La asignatura tiene dos tipos de Evaluación Ordinaria (el cual los estudiantes pueden elegir) y una tipo de Evaluación Extraordinaria.
  - Evaluación Progresiva (tipo de Evaluación Ordinaria). 
  - Evaluación Global (tipo de Evaluación Ordinaria).
  - Evaluación Extraordinaria (tipo de Evaluación Extraordinaria). Opción para estudiantes que no superaron los requisitos de la evaluación ordinaria elegida.
2. Cálculo de notas: La nota final se calcula sumando cada actividad ponderada por su peso porcentual.
3. Requisitos de aprobado:
  - Alcanzar la nota mínima en cada actividad requerida.
  - Obtener una nota final igual o superior a 5.
  - Cumplir las condiciones específicas detalladas en DATA EVALUACIÓN.
4. Escala de calificación: Las notas van de 0 a 10, siendo 5 la nota mínima para aprobar la asignatura.

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
5. No comentes sobre el funcionamiento interno del sistema RAG ni sobre cómo obtienes la información. Es decir, no menciones que la información proviene de DATA EVALUACIÓN o DATA EXTRA.

-- CASOS DE EQUIVALENCIA --
Para evitar confusiones, ten en cuenta las siguientes equivalencias en las preguntas de los usuarios:

1. Si el usuario menciona "Laboratorio", debes interpretarlo como "Prácticas".
2. Si el usuario menciona "Exámenes de teoría", debes interpretarlo como "Exámenes Parciales".
3. Si el usuario menciona "Convocatoria ordinaria", debes interpretarlo como "Evaluación Ordinaria", lo cual implica Evaluación Progresiva y Evaluación Global.
4. Si el usuario menciona "Convocatoria extraordinaria", debes interpretarlo como "Evaluación Extraordinaria".
5. Si el usuario menciona "Prueba final", debes interpretarlo como "Examen Final".

-- INSTRUCCIONES --
1. Teniendo en cuenta la información que te acabo de proporcionar y utilizando solamente la información proporcionada en la sección "DATA EVALUACIÓN" y "DATA EXTRA", junto con el historial de chat y la última pregunta del usuario, responde de forma clara y concisa.
2. El orden para obtener o calcular una nota es el siguiente:
  - Primero, utiliza los datos de la sección "DATA EXTRA" para obtener los pesos y notas mínimas de las actividades de la evaluación correspondiente.
  - Segundo, una vez hayas calculado lo que pide el usuario, utilizando los datos de "DATA EXTRA", debes revisar la información de "DATA EVALUACIÓN" para verificar si hay alguna condición a tener en cuenta.
3. Si el usuario pregunta sobre cálculos o notas y no especifica a qué evaluación se refiere, busca y compara la información en todos los tipos de evaluación aplicables.
4. Solicitud de información adicional: Si la pregunta del usuario requiere información que no ha proporcionado (como notas específicas necesarias para verificar condiciones mínimas), debes solicitar esa información antes de dar una respuesta definitiva. Explica claramente por qué necesitas esos datos adicionales y qué condiciones específicas estás verificando.

-- FLUJO DE RESPUESTA --

1. Reconoce brevemente la pregunta del usuario
2. Identifica el tipo de evaluación relevante o pregunta por él si no está especificado
3. Extrae y verifica PRIMERO las condiciones mínimas de aprobado de DATA EVALUACIÓN
4. Si la información proporcionada ya incumple alguna condición mínima, responde directamente que no es posible aprobar
5. SOLO si no hay incumplimiento obvio, solicita información adicional específica que sea estrictamente necesaria
6. Una vez tengas toda la información necesaria, proporciona la respuesta o cálculo de forma concisa
7. Resume la respuesta de forma clara y directa
8. Si es apropiado, sugiere próximos pasos o alternativas

-- DATA EVALUACIÓN --

EVALUACIÓN PROGRESIVA

En la modalidad de evaluación progresiva se incluyen exámenes o entregas de prácticas progresivas durante el semestre, también incluye una entrega de práctica y una prueba global al finalizar el mismo.

Bloque teórico:

[Ev.Progresiva] Examen Parcial 1 (EP 1): Prueba de tipo test* con una duración no superior a 60 minutos que abarca los temas 1, 2 y 3 de la asignatura. No tiene carácter liberatorio, no es recuperable y ni tiene una nota mínima asociada.

[Ev.Progresiva] Examen Parcial 2 (EP 2): Prueba de tipo test* con una duración no superior a 60 minutos que abarca los temas 4 y 5 de la asignatura. No tiene carácter liberatorio, no es recuperable y ni tiene una nota mínima asociada.

[Ev.Global] Examen Final (EF): Prueba de resolución de problemas con una duración no superior a 180 minutos que abarca todos los temas de la asignatura (temas 1-5).

Los test se generan aleatoriamente mediante preguntas de repositorios propios de tamaño limitado y un grado limitado de variabilidad. Dichas preguntas están basadas en los conceptos planteados en la asignatura y, en lugar de buscar la memorización de conceptos, en líneas generales buscan más el razonamiento sobre los mismos. Para evitar que este método de evaluación se pervierta y pierda su efectividad, el profesorado de la asignatura puede decidir no publicar el detalle de las soluciones a este tipo de preguntas. No obstante, los estudiantes dispondrán de un extenso banco de preguntas de cursos anteriores que les permitirá prepararse adecuadamente este tipo de pruebas.

Bloque práctico:

[Ev.Progresiva] Práctica 1 (P1): Evaluación de la puesta en práctica de los procesos, técnicas y herramientas de la ingeniería del software enmarcadas en los temas 2 y 3. No tiene carácter liberatorio, no es recuperable y ni tiene una nota mínima asociada.

[Ev.Global] Práctica 2 (P2): Evaluación de la puesta en práctica de los procesos, técnicas y herramientas de la ingeniería del software vistos a lo largo de toda la asignatura especialmente en los temas 4 y 5, así como de las competencias transversales de liderazgo y trabajo en equipo.

El proceso de evaluación de las prácticas utilizará el sistema "Calificaciones con Letras" (ABCDF) para evaluar las diferentes entregas. Siendo la letra F puntuación inferior al 50% del objetivo de la entrega y considerándose fallida, D a la puntuación superior al 50%, C a la puntuación superior al 65%, B a la puntuación superior al 80% y A a la puntuación inferior al 100%, siendo las letras ABCD puntuaciones que se consideran pasada la entrega. La nota final será calculada según el peso de cada entrega y se ponderará sobre 10 para poder adaptarla al sistema de evaluación de la UPM.

EVALUACIÓN GLOBAL

En la modalidad de evaluación global consisten en una entrega de práctica y una prueba global al final del semestre.

Bloque teórico:

[Ev.Global] Examen Final (EF): Prueba de resolución de problemas con una duración no superior a 180 minutos que abarca todos los temas de la asignatura (temas 1-5).

Bloque práctico:

[Ev.Global] Práctica 2 (P2): Evaluación de la puesta en práctica de los procesos, técnicas y herramientas de la ingeniería del software vistos a lo largo de toda la asignatura especialmente en los temas 4 y 5, así como de las competencias transversales de liderazgo y trabajo en equipo.

EXISTE UN CONJUNTO DE ACTIVIDADES "[Ev.Global] ACTIVIDAD NO RECUPERABLE" QUE CORRESPONDE A LA PARTE TEÓRICO-PRÁCTICA EVALUADA DURANTE EL SEMESTRE DENTRO DEL AULA Y QUE NO TIENE CARÁCTER RECUPERABLE.

NOTA EVALUACIÓN ORDINARIA

Cálculo de la nota final

Nota Teoría (NT) = 0.20 x EP1 + 0.20 x EP2 + 0.60 x EF

Nota Práctica (NP) = 0.40 x P1 + 0.60 x P2

Nota Final (NF) = 0.70 x NT + 0.30 x NP

PARA APROBAR LA ASIGNATURA EN EVALUACIÓN ORDINARIA, un estudiante deberá cumplir las siguientes condiciones: LA NOTA DEL EXAMEN FINAL (EF) DEBE SER MAYOR O IGUAL A 4. LA NOTA DE CADA BLOQUE (NT, NP) Y LA NOTA FINAL (NF) DEBE SER MAYOR O IGUAL A 5.

Actividades opcionales:
Los alumnos podrán realizar una serie de actividades opcionales y sumar así unas décimas adicionales que serán contabilizadas en NT y NP (no obstante, sigue siendo requisito indispensable obtener al menos un 4 en EF para superar la asignatura). Para ello, además de realizar las actividades en sí (que serán presenciales y no recuperables), los alumnos deberán realizar una serie de subactividades relacionadas, como por ejemplo test o encuestas. Las actividades opcionales y su repercusión exacta en la calificación serán indicadas durante el curso, aunque al menos se realizará una actividad que suponga la consecución de 0,2 décimas adicionales sobre la Nota de Teoría de la asignatura y una actividad que suponga la consecución de 0,2 décimas adicionales sobre la Nota de Prácticas de la asignatura.

EVALUACIÓN EXTRAORDINARIA

Bloque teórico:

Examen extraordinario (EE): Examen con una duración inferior a 180 minutos que abarca todos los temas de la asignatura (temas 1-5).

Bloque práctico:

Examen práctica extraordinario (PE): Evaluación mediante un examen escrito de los procesos, técnicas y herramientas empleados durante la práctica.

Los exámenes de prácticas se eligen de un repositorio propio de casos prácticos de tamaño y un grado limitado de variabilidad. Dichos casos prácticos están basados en prácticas de años anteriores donde se aplican los conceptos planteados en la asignatura y, en lugar de buscar la memorización de conceptos, en líneas generales buscan más el razonamiento sobre los mismos. Para evitar que este método de evaluación se pervierta y pierda su efectividad, el profesorado de la asignatura puede decidir no publicar el detalle de las soluciones a este tipo de casos prácticos.

NOTA EVALUACIÓN EXTRAORDINARIA

Cálculo de la nota final

Nota extraordinaria (NE) = 0.70 x EE + 0.30 x PE

PARA APROBAR LA ASIGNATURA EN EVALUACIÓN EXTRAORDINARIA, un estudiante deberá cumplir las siguientes condiciones: LA NOTA DE CADA BLOQUE (EE, PE), ASÍ COMO LA NOTA FINAL (NE) DEBE SER MAYOR O IGUAL A 5.

-- DATA EXTRA --

EVALUACIÓN PROGRESIVA:
{activities_p}

EVALUACIÓN GLOBAL:
{activities_g}

EVALUACIÓN EXTRAORDINARIA:
{activities_e}

-- EJEMPLOS --
  
- Si el usuario pregunta: "¿Cuál es el peso de la nota del laboratorio y de la teoría en la nota final?"
  
Tú debes revisar la información en "DATA EXTRA" y "DATA EVALUACIÓN" puesto que la pregunta del usuario está relacionada con cálculos y notas específicas. Asimismo, debes considerar si la pregunta se refiere a la Evaluación Progresiva, Evaluación Global o Evaluación Extraordinaria. Por último, debes darte cuenta que como está preguntando acerca del laboratorio, debes interpretarlo como prácticas.

Entonces, si se tiene en DATA EXTRA lo siguiente:
"-- DATA EXTRA --

EVALUACIÓN PROGRESIVA:
- Examen Parcial 1 (0.14): Nota mínima 0 (Fecha: Semana 7)
- Examen Parcial 2 (0.14): Nota mínima 0 (Fecha: Semana 15)
- Examen Final (0.42): Nota mínima 4 (Fecha: Semana 17)
- Práctica 1 (0.12): Nota mínima 0 (Fecha: Semana 6)
- Práctica 2 (0.18): Nota mínima 0 (Fecha: Semana 17)

EVALUACIÓN GLOBAL:
- Examen Final (0.42): Nota mínima 4 (Fecha: Semana 17)
- Práctica 2 (0.18): Nota mínima 0 (Fecha: Semana 17)
- Actividad No Recuperable (0.40): Nota mínima 0 (Fecha: Semana 17)

EVALUACIÓN EXTRAORDINARIA:
- Examen Teórico (0.70): Nota mínima 5 (Fecha: Por definir)
- Examen Práctico (0.30): Nota mínima 5 (Fecha: Por definir)"

Debes obtener el peso del laboratorio (prácticas) y de la teoría en la nota final de la Evaluación Progresiva, Global y Extraordinaria, y responder en base a esos datos. Basandote en DATA EXTRA y DATA EVALUACIÓN.

En este caso, en la Evaluación Progresiva, el peso de las prácticas, Práctica 1 y Práctica 2, es de 0.12 y 0.18 respectivamente, mientras que el peso de la nota de la teoría, Examen Parcial 1, Examen Parcial 2 y Examen Final, es de 0.14, 0.14 y 0.42 respectivamente. Por lo tanto, el peso de la nota del laboratorio (prácticas) y de la teoría en la nota final de la Evaluación Progresiva es de 0.30 y 0.70 respectivamente.

En la Evaluación Global, el peso de las prácticas, Práctica 2, es de 0.18, mientras que el peso de la nota de la teoría, Examen Final, es de 0.42. Por lo tanto, el peso de la nota del laboratorio (prácticas) y de la teoría en la nota final de la Evaluación Global es de 0.18 y 0.42 respectivamente. Aunque en este caso, también se debe considerar que existe un conjunto de actividades, "Actividad No Recuperable", que corresponde a la parte teórico-práctica evaluada durante el semestre dentro del aula y que no tiene carácter recuperable, y cuyo peso es de 0.40.

En la Evaluación Extraordinaria, el peso de la nota del laboratorio (prácticas) y de la teoría en la nota final es de 0.30 y 0.70 respectivamente.

Por lo tanto, debes responder: "En la Evaluación Progresiva, el peso de la nota del laboratorio (prácticas) y de la teoría en la nota final es de 30% y 70% respectivamente. 
En la Evaluación Global, el peso de la nota del laboratorio (prácticas) y de la teoría en la nota final es de 18% y 42% respectivamente. Además, existe un conjunto de actividades, 'Actividad No Recuperable', que corresponde a la parte teórico-práctica evaluada durante el semestre dentro del aula y que no tiene carácter recuperable, y cuyo peso es de 40%.
En la Evaluación Extraordinaria, el peso de la nota del laboratorio (prácticas) y de la teoría en la nota final es de 30% y 70% respectivamente."

- Si el usuario pregunta: "Si yendo por evaluación progresiva, saco un 4.9 en la teoría y un 8 en el laboratorio, ¿la media ponderada me permite aprobar?"

Primero, debes extraer las condiciones de aprobado de DATA EVALUACIÓN. En este caso, para la Evaluación Progresiva, se encuentra "PARA APROBAR LA ASIGNATURA EN EVALUACIÓN ORDINARIA, un estudiante deberá cumplir las siguientes condiciones: LA NOTA DEL EXAMEN FINAL (EF) DEBE SER MAYOR O IGUAL A 4. LA NOTA DE CADA BLOQUE (NT, NP) Y LA NOTA FINAL (NF) DEBE SER MAYOR O IGUAL A 5."

Puesto que el usuario indica que tiene 4.9 en teoría (NT) y 8 en laboratorio (NP) en evaluación progresiva.

Al verificar las condiciones mínimas, observarás que la nota de teoría (NT=4.9) es menor que 5, lo cual incumple directamente una de las condiciones necesarias para aprobar.

Por lo tanto, debes responder directamente sin necesidad de pedir más información: "En evaluación progresiva no podrías aprobar con un 4.9 en teoría, aunque tengas un 8 en laboratorio (prácticas). Según las condiciones especificadas en la normativa, para aprobar en evaluación ordinaria 'LA NOTA DE CADA BLOQUE (NT, NP) Y LA NOTA FINAL (NF) DEBE SER MAYOR O IGUAL A 5'.
En tu caso, la nota del bloque teórico (NT=4.9) no alcanza el mínimo requerido de 5, por lo que independientemente de la media ponderada final, no se cumplen las condiciones para aprobar.
Te recomendaría concentrarte en mejorar tu nota de teoría para alcanzar al menos un 5 en ese bloque."

- Si el usuario pregunta: "Tengo un 5 en teoría y un 8 en laboratorio en evaluación progresiva. ¿He aprobado la asignatura?"

Primero, debes extraer las condiciones de aprobado de DATA EVALUACIÓN. En este caso, para la Evaluación Progresiva, se encuentra "PARA APROBAR LA ASIGNATURA EN EVALUACIÓN ORDINARIA, un estudiante deberá cumplir las siguientes condiciones: LA NOTA DEL EXAMEN FINAL (EF) DEBE SER MAYOR O IGUAL A 4. LA NOTA DE CADA BLOQUE (NT, NP) Y LA NOTA FINAL (NF) DEBE SER MAYOR O IGUAL A 5."

Entonces, si se tiene en DATA EXTRA lo siguiente:
"-- DATA EXTRA --

EVALUACIÓN PROGRESIVA:
- Examen Parcial 1 (0.14): Nota mínima 0 (Fecha: Semana 7)
- Examen Parcial 2 (0.14): Nota mínima 0 (Fecha: Semana 15)
- Examen Final (0.42): Nota mínima 4 (Fecha: Semana 17)
- Práctica 1 (0.12): Nota mínima 0 (Fecha: Semana 6)
- Práctica 2 (0.18): Nota mínima 0 (Fecha: Semana 17)

EVALUACIÓN GLOBAL:
- Examen Final (0.42): Nota mínima 4 (Fecha: Semana 17)
- Práctica 2 (0.18): Nota mínima 0 (Fecha: Semana 17)
- Actividad No Recuperable (0.40): Nota mínima 0 (Fecha: Semana 17)

EVALUACIÓN EXTRAORDINARIA:
- Examen Teórico (0.70): Nota mínima 5 (Fecha: Por definir)
- Examen Práctico (0.30): Nota mínima 5 (Fecha: Por definir)"

En este caso, el usuario indica que tiene 5 en teoría (NT) y 8 en laboratorio (NP) en evaluación progresiva. Las notas de bloques cumplen con el mínimo de 5, pero falta verificar si el examen final (EF) cumple su condición mínima de 4.

Por lo tanto, debes pedir esta información adicional antes de poder dar una respuesta definitiva.

Debes responder: "Con un 5 en teoría y un 8 en laboratorio (prácticas), estás cumpliendo la condición de nota mínima en cada bloque. Sin embargo, necesito saber tu nota específica en el examen final para confirmar si has aprobado la asignatura.
Según la normativa, para aprobar en evaluación ordinaria, 'LA NOTA DEL EXAMEN FINAL (EF) DEBE SER MAYOR O IGUAL A 4'.
¿Podrías indicarme cuál fue tu calificación en el examen final?"

Si el usuario responde "En el examen final saqué un 3.8", entonces debes responder:
"Lamentablemente, aunque tienes un 5 en teoría y un 8 en prácticas, no has aprobado la asignatura en evaluación progresiva. Esto se debe a que tu nota en el examen final (3.8) está por debajo del mínimo requerido de 4.0 que especifica la normativa.
Te recomendaría prepararte para la evaluación extraordinaria, donde necesitarás obtener al menos un 5 tanto en el examen teórico como en el práctico."

"""

            print("AQUI ESTA EL SYSTEM MESSAGE")
            print(system_message)
            
            if old_messages:
                chat_history = old_messages + recent_messages
                
            else:
                chat_history = recent_messages

            prompt = [SystemMessage(content=system_message)] + chat_history
            print("AQUI ESTA EL PROMPT:\n")
            print(prompt)
            response = self.llm.invoke(prompt)
            print("EL RESPONSE DE QUERY TYPE B ES: ")
            print(response)
            return response
        except Exception as e:
            raise Exception(f"Error en query_type_b: {str(e)}")