import os
import uvicorn
from app import create_app
from dotenv import load_dotenv  

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path)

print("CHROMADB_PORT:", os.getenv("CHROMADB_PORT"))  # Debería imprimir 8001

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
