import re

def extract_primary_email(value):
    if not value:
        return None

    value = str(value)

 
    parts = re.split(r"[,\n ]+", value)

    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    for part in parts:
        part = part.strip().lower()
        if re.match(email_regex, part):
            return part

    return None

def clean_phone(value):
    if not value:
        return None
    return str(value).strip()

def clean_string(value):
    if value is None:
        return None
    return str(value).strip()