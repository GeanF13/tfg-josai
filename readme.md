Usando python 3.13

Necesito chroma db corriendo en el 8001


Desde la carpeta backend: chroma run --host localhost --port 8001
Desde la carpeta backend: uvicorn main:app --reload
Desde la carpeta frontend: streamlit run app.py


pip install -U langchain-community
pip install langchain langchain-community ollama


export $(cat ".env-example" | sed 's/#.*//g' | xargs)

chroma run --host localhost --port 8001


pip install pdfplumber
pip install unidecode
pip install python-multipart
pip install langchain_ollama
pip install pypdf

instalar ollama: curl -fsSL https://ollama.com/install.sh | sh

ollama pull nomic-embed-text
ollama pull llama3.2

pip install --upgrade --quiet langgraph langchain-community beautifulsoup4
ollama pull deepseek-r1:14b
pip install -qU langchain-deepseek