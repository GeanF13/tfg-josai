import streamlit as st
import requests
import uuid
import json
import time
from typing import Dict, List
import pandas as pd
import base64
from PIL import Image
import io
import os

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

# CSS personalizado para sobrescribir el color de texto resaltado
st.markdown("""
<style>
/* Sobrescribir el color de fondo de código inline y texto resaltado */
code {
    background-color: #E8E8E8 !important;
    color: #333333 !important;
    padding: 2px 4px;
    border-radius: 3px;
}

/* Sobrescribir elementos con background secundario problemático */
.stMarkdown code {
    background-color: #F0F0F0 !important;
    color: #2C2C2C !important;
}

/* Mantener el sidebar con tu color azul */
.css-1d391kg {
    background-color: #1B72BF !important;
}

/* Asegurar que el texto del sidebar sea legible */
.css-1d391kg .stMarkdown {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# Función para convertir imagen a base64
def get_image_base64(image_path):
    if not os.path.isfile(image_path):
        return None
    
    img = Image.open(image_path)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Rutas a tus imágenes de avatar
ai_avatar_path = "assets/ai_icon.png"
user_avatar_path = "assets/user_icon.png"

# Convertir imágenes a formato base64
ai_avatar_base64 = get_image_base64(ai_avatar_path)
user_avatar_base64 = get_image_base64(user_avatar_path)

# Crear las URLs de datos
ai_avatar = f"data:image/png;base64,{ai_avatar_base64}" if ai_avatar_base64 else None
user_avatar = f"data:image/png;base64,{user_avatar_base64}" if user_avatar_base64 else None


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
st.title("🤖 JosAI - Asistente de Información sobre las asignaturas de la ETSISI")

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
    
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    logo_path = "assets/logo_etsisi.png"
    st.image(logo_path, width=150, use_container_width=False)

# Área principal de chat
if st.session_state.selected_guide:
    # Mostrar el nombre de la guía seleccionada
    subject_name = guide_options.get(st.session_state.selected_guide, "Guía seleccionada")
    st.subheader(f"Chat sobre: **{subject_name.capitalize()}**")
    
    # Mostrar mensajes anteriores
    for message in st.session_state.messages:
        avatar = ai_avatar if message["role"] == "assistant" else user_avatar
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    
    # Input para nuevo mensaje
    if prompt := st.chat_input("Escribe tu pregunta sobre la guía docente..."):
        # Mostrar el mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(prompt)
        
        # Enviar mensaje al backend y mostrar respuesta
        with st.chat_message("assistant", avatar=ai_avatar):
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
    