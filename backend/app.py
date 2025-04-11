from fastapi import FastAPI
from api import teaching_guide
from api import chat
from api import faq
from dotenv import load_dotenv

load_dotenv()

def create_app() -> FastAPI:
    app = FastAPI(
        title = "JosAI API",
        description = "API for JosAI",
        version = "0.1"
    )

    app.include_router(teaching_guide.router)
    app.include_router(chat.router)
    app.include_router(faq.router)
    
    return app
