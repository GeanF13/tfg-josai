import streamlit as st
import requests
import uuid
import json
import time
from typing import Dict, List
import pandas as pd

# URL base de tu API (ajusta según tu configuración)
API_BASE_URL = "http://localhost:8000"

# Configuración de la página
st.set_page_config(
    page_title='JosAI',
    page_icon='🤖',
    layout="wide",
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'https://www.etsisi.upm.es',
        'About': 'This is a chatbot that helps you with the subjects of the ETSISI'
    }
)

# Función para cargar una guía docente
def upload_teaching_guide(file):
    if file is None:
        return False, "No se ha seleccionado ningún archivo"
    
    # Crear un formulario de datos con el archivo
    files = {"guide": (file.name, file.getvalue(), "application/pdf")}
    
    try:
        response = requests.post(f"{API_BASE_URL}/upload-teaching-guide/", files=files)
        response.raise_for_status()  # Lanzar excepción si la respuesta indica error
        return True, response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            return False, e.response.json().get("detail", "Error en la solicitud")
        else:
            return False, f"Error en el servidor: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

# Función para obtener todas las guías docentes disponibles
def get_all_teaching_guides():
    try:
        response = requests.get(f"{API_BASE_URL}/teaching-guides/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener las guías docentes: {str(e)}")
        return []

# Función para manejar la subida de preguntas frecuentes
def upload_faq(file, subject_id):
    if file is None:
        return False, "No se ha seleccionado ningún archivo"
    
    # Crear un formulario de datos con el archivo
    files = {"faq": (file.name, file.getvalue(), "application/pdf")}
    
    try:
        response = requests.post(f"{API_BASE_URL}/upload-faq/{subject_id}", files=files)
        response.raise_for_status()
        return True, response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            return False, e.response.json().get("detail", "Error en la solicitud")
        else:
            return False, f"Error en el servidor: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

# Función para enviar un mensaje al chat
def send_chat_message(subject_id, user_query, thread_id=None):
    try:
        payload = {
            "subject_id": subject_id,
            "user_query": user_query
        }
        
        if thread_id:
            payload["thread_id"] = thread_id
            
        response = requests.post(f"{API_BASE_URL}/chat/", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al enviar mensaje: {str(e)}")
        return None

# Inicializar variables de estado en session_state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'selected_guide' not in st.session_state:
    st.session_state.selected_guide = None
if 'guides' not in st.session_state:
    # Intentar cargar las guías docentes al inicio
    st.session_state.guides = get_all_teaching_guides()

# Título principal
st.title("Asistente de Guías Docentes")

# Sidebar para subir guías y seleccionarlas
with st.sidebar:
    st.header("Guías Docentes")
    
    # Botón para subir nueva guía
    st.subheader("Subir nueva guía docente")
    uploaded_file = st.file_uploader("Selecciona un archivo PDF", type="pdf")
    
    if st.button("Procesar Guía"):
        if uploaded_file:
            with st.spinner("Procesando guía docente..."):
                success, result = upload_teaching_guide(uploaded_file)
                if success:
                    st.success(f"Guía docente procesada correctamente: {result['guia_docente']}")
                    # Actualizar la lista de guías
                    st.session_state.guides = get_all_teaching_guides()
                    # Seleccionar automáticamente la guía recién subida
                    st.session_state.selected_guide = result['id']
                    # Reiniciar el chat
                    st.session_state.messages = []
                    st.session_state.thread_id = None
                    st.rerun()
                else:
                    st.error(f"Error: {result}")
        else:
            st.warning("Por favor, selecciona un archivo PDF primero")
    
    # Dropdown para seleccionar guía
    st.subheader("Seleccionar guía docente")
    
    # Crear un diccionario subject_id -> nombre para el dropdown
    guide_options = {}
    if st.session_state.guides:
        for guide in st.session_state.guides:
            guide_options[guide['id']] = guide['name']
    
    # Si hay guías disponibles, mostrar el dropdown
    if guide_options:
        selected_id = st.selectbox(
            "Elige una guía docente",
            options=list(guide_options.keys()),
            format_func=lambda x: guide_options[x],
            key="guide_selector"
        )
        
        # Si se selecciona una guía diferente, reiniciar el chat
        if selected_id != st.session_state.selected_guide:
            st.session_state.selected_guide = selected_id
            st.session_state.messages = []
            st.session_state.thread_id = None
            st.rerun()
            
            
        # Mostrar sección de subida de preguntas frecuentes
        if st.session_state.selected_guide:
            st.markdown("---")
            st.subheader("Preguntas Frecuentes")
            uploaded_faq = st.file_uploader("Selecciona un archivo PDF con preguntas frecuentes", type="pdf", key="faq_uploader")
            
            if st.button("Procesar Preguntas Frecuentes"):
                if uploaded_faq:
                    with st.spinner("Procesando preguntas frecuentes..."):
                        success, result = upload_faq(uploaded_faq, st.session_state.selected_guide)
                        if success:
                            st.success("Preguntas frecuentes procesadas correctamente")
                        else:
                            st.error(f"Error: {result}")
                else:
                    st.warning("Por favor, selecciona un archivo PDF primero")
        
    else:
        st.info("No hay guías docentes disponibles. Sube una para comenzar.")

# Área principal de chat
if st.session_state.selected_guide:
    # Mostrar el nombre de la guía seleccionada
    st.subheader(f"Chat sobre: {guide_options.get(st.session_state.selected_guide, 'Guía seleccionada')}")
    
    # Mostrar mensajes anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input para nuevo mensaje
    if prompt := st.chat_input("Escribe tu pregunta sobre la guía docente..."):
        # Mostrar el mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Enviar mensaje al backend y mostrar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response_data = send_chat_message(
                    st.session_state.selected_guide, 
                    prompt, 
                    st.session_state.thread_id
                )
                
                if response_data:
                    # Guardar el thread_id para futuros mensajes
                    st.session_state.thread_id = response_data["thread_id"]
                    
                    # Mostrar la respuesta
                    st.markdown(response_data["response"])
                    
                    # Añadir al historial
                    st.session_state.messages.append({"role": "assistant", "content": response_data["response"]})
                else:
                    st.error("No se pudo obtener una respuesta. Por favor, intenta de nuevo.")
else:
    # Si no hay guía seleccionada
    st.info("Selecciona una guía docente en el panel lateral para comenzar a chatear.")