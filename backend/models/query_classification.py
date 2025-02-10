from pydantic import BaseModel, Field

class QueryClassification(BaseModel):
    category: str = Field(
        description="La categoría de la pregunta del usuario debe ser una de: A, BP, BG, BE, BT o C"
    )