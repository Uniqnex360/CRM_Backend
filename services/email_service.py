import httpx
from dotenv import load_dotenv
import os
load_dotenv()
BREVO_API_KEY = os.getenv("BREVO_API_KEY")   
# print("API KEY:", BREVO_API_KEY)
if not BREVO_API_KEY:
    raise Exception("BREVO_API_KEY is missing in environment variables")
async def send_email(to_email:str,subject: str, html_content: str):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",   
        "api-key": str(BREVO_API_KEY),
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
    print("SENDING EMAIL TO:", to_email)
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        print("STATUS CODE:", response.status_code)
        print("RAW TEXT:", response.text)
    # data = response.json()
    # print("Brevo response:",data) 
        try:
             data = response.json()
        except Exception:
            data = None

        print("PARSED JSON:", data)
   

    if response.status_code not in [200, 201, 202]:
        raise Exception(f"Email failed: {response.text}")

    return data