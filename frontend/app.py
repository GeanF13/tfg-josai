import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title='JosAI',
    page_icon='🤖',
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'https://www.etsisi.upm.es',
        'About': 'This is a chatbot that helps you with the subjects of the ETSISI'
    }
)

st.markdown("""
    <style>
        .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

# Función para subir guías docentes
def upload_teaching_guide(file):
    files = {"guide": (file.name, file.getvalue(), "application/pdf")}
    response = requests.post(f"{API_URL}/upload-teaching-guide/", files=files)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Error al subir la guía docente."}


# Función para enviar consultas al chatbot
def chat_with_bot(user_query, subject_id):
    payload = {"subject_id": subject_id, "user_query": user_query}
    response = requests.post(f"{API_URL}/chat/", json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Error en la comunicación con el chatbot."}

# 📌 Sidebar de Streamlit
with st.sidebar:
    st.title('💬 JosAI')
    
    # 📚 Subida de archivos PDF
    file_uploaded = st.file_uploader(
        "Subir guía docente (PDF)", type=["pdf"]
    )
    
    if st.button("Procesar Guía"):
        if file_uploaded:
            with st.spinner("Procesando la guía docente..."):
                result = upload_teaching_guide(file_uploaded)
                st.success("¡Guía docente subida correctamente!")
                st.write(result)
        else:
            st.warning("Por favor, sube un archivo PDF.")

# 📌 Sección de Chat
st.subheader("Chat con JosAI 🤖")

# 📚 Seleccionar una guía docente disponible
subject_id = st.text_input("Introduce el ID de la guía docente:")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte con la guía docente?"}
    ]

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
        st.write(message["content"])

# Entrada del usuario
user_query = st.chat_input("Escribe tu pregunta...", disabled=not subject_id)

if user_query:
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar="👤"):
        st.write(user_query)

    with st.spinner("Pensando..."):
        response = chat_with_bot(user_query, subject_id)

    # Agregar respuesta del chatbot
    if "response" in response:
        bot_response = response["response"]
        with st.chat_message("assistant", avatar="🤖"):
            st.write(bot_response)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
    else:
        st.error("Hubo un error al procesar la respuesta.")
    
