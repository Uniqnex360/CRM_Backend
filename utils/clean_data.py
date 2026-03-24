import re
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
from typing import List
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def extract_primary_email(value):

    if pd.isna(value) or value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    parts = re.split(r"[,\n; ]+", value)

    for part in parts:
        part = part.strip().lower()
        if EMAIL_REGEX.match(part):
            return part

    return None


def clean_phone(value):

    if pd.isna(value) or value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    value = re.sub(r"[^\d+]", "", value)

    return value or None


def clean_string(value):
    
    if pd.isna(value) or value is None:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    value = str(value).strip()

    return value or None

def normalize_company_name(name):
    if not name:
        return None

    import re
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()





def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    # text = re.sub(r"(.)\1+", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_name(text):
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def make_regex(text: str):
    if not text:
        return ""
    
    text = normalize_text(text)
    words = text.split()
    regex = ".*".join(words)
    return f".*{regex}.*"



def normalize_regex_title(text: str):
    if not text:
        return ""
    text = normalize_name(text)  
    words = [re.escape(word) for word in text.split()]
    return r"[\s\W]*".join(words)


def normalize_fuzzy_regex(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]", "", text)  
    regex = r".*".join(list(text))    
    return regex

def normalize_fuzzy_regex_safe(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w]", "", text)  
    if len(text) < 4:
       
        return f".*{text}.*"
   
    return r".*".join(list(text))

def normalize_sort(value):
    if not value:
        return " "

    value = str(value).lower().strip()
    value = re.sub(r"[|@]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def location_regex(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)     
    text = re.sub(r"\s+", " ", text).strip()

    if " " in text:
        return ".*".join(text.split())
    return ".*".join(list(text))


def ncity_regex(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    if len(words) > 1:
        return ".*".join(words) 
    else:
        return ".*".join(list(words[0]))
    
    import re

def clean_company_name(name: str) -> str:
    if not name:
        return name
    name = re.sub(r'[\u200B-\u200D\uFEFF]', '', name)
    name = name.replace('"', '').replace("'", "")
    name = re.sub(r"[()]", "", name)
    name = re.sub(r"\s+", " ", name)

    return name.strip()

def clean_roles(raw_string):
    if not raw_string:
        return []
    cleaned = re.sub(r'\|+', '|', raw_string).strip('|').strip()
    parts = re.split(r'\||,', cleaned)
    roles = [p.strip() for p in parts if p.strip()]
    return "; ".join(parts)

def clean_part(value):
        if not value:
            return None

        value = str(value)
        value = re.sub(r'[\u200B-\u200D\uFEFF]', '', value)
        value = value.replace("-", "").strip()
        value = re.sub(r',+', '', value)
        value = re.sub(r'\s+', ' ', value)

        if value.lower() in ["", "none", "null"]:
            return None

        return value.strip()
def clean_location_fields(city, state, country):
    city = clean_part(city)
    state = clean_part(state)
    country = clean_part(country)
    parts = [p for p in [city, country] if p]

    location = ", ".join(parts) if parts else None

    return city, state, country, location
