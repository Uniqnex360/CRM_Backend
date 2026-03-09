import re
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
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


def is_similar(a, b, threshold=80):
    a = normalize_text(a)
    b = normalize_text(b)
    return fuzz.ratio(a, b) >= threshold


def normalize_fuzzy_regex(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]", "", text)  
    regex = r".*".join(list(text))    
    return regex