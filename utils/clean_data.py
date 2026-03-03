import re
import pandas as pd
from datetime import datetime

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