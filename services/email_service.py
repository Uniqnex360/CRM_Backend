import httpx
from dotenv import load_dotenv
import os
load_dotenv()
BREVO_API_KEY = os.getenv("BREVO_API_KEY")   
# print("API KEY:", BREVO_API_KEY)
async def send_email(to_email:str,subject: str, html_content: str):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "CRM",
            "email": "sangamithra@uniqnex360.com"
        },
        "to": [
            {"email":to_email}
        ],
        "subject": subject,
        "htmlContent":html_content
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)

    print("Brevo response:", response.status_code, response.text)

    if response.status_code not in [200, 201, 202]:
        raise Exception(f"Email failed: {response.text}")

    return True