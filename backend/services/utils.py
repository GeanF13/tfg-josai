import re

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

def from_activities_list_to_string(activities, assessment_type):
    string = f"En la {assessment_type} se encuentran las siguientes actividades: \n"
    for activity in activities:
        modality = activity[2].split(":")[1].strip()
        name = activity[3]
        percentage = activity[4]
        passing_grade = activity[5]
        date = activity[6]
        string += f"El nombre de la actividad es {name}, su modalidad es {modality}, con un peso en la nota final de {percentage}% y una nota mínima de {passing_grade}"
        string += f"Ademas, la fecha en la que se realizará es en la semana {date}" if date != 0 else ""
        string += "\n"
    return string