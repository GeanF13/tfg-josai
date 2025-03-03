import re
from langchain_core.messages import HumanMessage, AIMessage
import json

def get_subject_id(filename):
    """Summary

    Args:
        filename (str): Name of the file

    Returns:
        str: Code of the subject
    """
    match = re.search(r'_(\d+)_', filename)
    if match:
        return match.group(1)
    else:
        return None
    
def extract_number(text):
    match = re.search(r'(\d*)\s*/', text)
    if match:
        number = match.group(1).strip()
        return int(number) if number != '' else 0
    else:
        return 0

def from_activities_list_to_string(activities: dict, assessment_type):
    string = f"En la {assessment_type} se encuentran las siguientes actividades: \n"
    for activity in activities:
        modality = activity["modality"].split(":")[1].strip()
        #modality = activity[2].split(":")[1].strip()
        name = activity["name"]
        #name = activity[3]
        percentage = activity["percentage"]
        #percentage = activity[4]
        passing_grade = activity["passing_grade"]
        #passing_grade = activity[5]
        date = activity["date"]
        #date = activity[6]
        string += f"El nombre de la actividad es {name}, su modalidad es {modality}, con un peso en la nota final de {percentage}% y una nota mínima de {passing_grade}. "
        if date != 0:
            string += f"Además, la fecha en la que se realizará es en la semana {date}"
        else:
            string += "La fecha de la actividad no ha sido definida"
        string += "\n"
    
    return string

def transform_activity(activity):
    modality = activity["modality"].split(":")[1].strip()
    name = activity["name"]
    percentage = f"{activity["percentage"]}%"
    passing_grade = activity["passing_grade"]
    date = activity["date"]
    if date != 0:
        date = f"La actividad se realizará en la semana {date}"
    else:
        date = "La fecha de la actividad no ha sido definida"
    
    return {
        "actividad": name,
        "modalidad": modality,
        "peso": percentage,
        "nota_minima": passing_grade,
        "fecha": date
    }

def generate_data_extra(activities_p: dict, activities_g: dict, activities_e: dict):
    data_extra = {
        "evaluacion progresiva": [transform_activity(activity) for activity in activities_p],
        "evaluacion global": [transform_activity(activity) for activity in activities_g],
        "evaluacion extraordinaria": [transform_activity(activity) for activity in activities_e]
    }
    data_extra = json.dumps(data_extra, indent=2, ensure_ascii=False)
    return data_extra

def generate_activities(activities: dict):
    string = ""
    for activity in activities:
        name = activity["name"]
        modality = activity["modality"].split(":")[1].strip()
        if modality.startswith("tecnica del tipo "):
            modality = modality[len("tecnica del tipo "):]
        percentage = activity["percentage"]
        passing_grade = activity["passing_grade"]
        date = activity["date"]
        string += f"- {name.capitalize()} (0.{percentage}): Nota mínima {passing_grade} (Fecha: "
        #string += f"  - Modalidad: {modality}\n"
        #string += f"  - Nota mínima: {passing_grade}\n"
        if date != 0:
            string += f"Semana {date})\n"
        else:
            string += "Por definir)\n"
    
    return string

def get_role(fragment):
    if fragment.content.startswith("Resumen:"):
        return "Resumen anterior"
    elif isinstance(fragment, HumanMessage):
        return "Humano"
    elif isinstance(fragment, AIMessage):
        return "IA"
    else:
        return "Desconocido"