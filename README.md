##### CRM Backend API

A scalable CRM Backend built using FastAPI, JWT Authentication, and MongoDB.
This project handles user authentication, lead management, and business validation logic.

Features

User Registration & Login

JWT Authentication

Protected Routes

Lead Management (Create, Read, Update, Delete)

Business Validation Layer

MongoDB Integration

Pydantic Schema Validation

Tech Stack

Backend Framework: FastAPI

Server: Uvicorn

Database: MongoDB

Authentication: JSON Web Token

Password Hashing: bcrypt

Validation: Pydantic 


##### RENDER URL :https://crm-backend-4807.onrender.com
######  Project Structure
crm_backend/ -->
│
├── main.py
├── database.py
├── api/
│     ├── leads.py
│     └── user.py
│
├── auth/
│     ├── create_access.py
│     └── login.py
│
├── export/
│     └── export_leads.py
│
├── schemas/
│     ├── user_schema.py
│     └── lead_schema.py
│
├── services/
│     └── create_or_import.py
|___utils
|      |___company_resolve.py
│
└── README.md -->


Authentication Flow

User registers

Password is hashed using bcrypt

User logs in

JWT access token is generated

Protected routes require Authorization: Bearer <token> 


AUTHENTICATON

| Method | Endpoint | Description                |
| ------ | -------- | -------------------------- |
| POST   | /signup  | Register new user          |
| POST   | /login   | Login and get JWT token    |
| GET    | /me      | Get current logged-in user |


USER 

| Method | Endpoint    | Description       | Auth Required |
| ------ | ----------- | ----------------- | ------------- |
| GET    | /users      | List all users    | Yes           |
| GET    | /users/{id} | Get user by ID    | Yes           |
| PUT    | /users/{id} | Update user by ID | Yes           |
| DELETE | /users/{id} | Delete user by ID | Yes           |


LEADS 

| Method | Endpoint                 | Description                      | Auth Required |
| ------ | ------------------------ | -------------------------------- | ------------- |
| POST   | /leads/create_leads      | Create a lead / upload CSV/excel | Yes           |
| GET    | /leads/read_leads        | List all leads for current user  | Yes           |
| GET    | /leads/read_leads/{id}   | Get a single lead                | Yes           |
| PUT    | /leads/update_leads/{id} | Update a lead                    | Yes           |
| PATCH  | /leads/leads_status/{id} | active/inactive and add to fav   | Yes           |

COMPANY

| Method | Endpoint                     | Description                           | Auth Required |
| ------ | ------------------------     | --------------------------------      | ------------- |
| POST   | /company/create_company      | Create a company / upload CSV/excel   | Yes           |
| GET    | /company/read_company        | List all companies for current user   | Yes           |
| GET    | /company/read_company/{id}   | Get a single company                  | Yes           |
| PUT    | /company/update_company/{id} | Update a company                      | Yes           |
| PATCH  | /company/company_status/{id} | active/inactive and add to fav        | Yes           |

LISTS


| Method | Endpoint                     | Description                           | Auth Required |
| ------ | ------------------------     | --------------------------------      | ------------- |
| POST   | /list/create_list            |   Create a list                       | Yes           |
| GET    | /list/view_lists             |   All available lists                 | Yes           |
| POST   | /list/{list_id}/add_members  |   Add members to the list             | Yes           |
| GET    | /list/{list_id}/view_members |  view members from the list           | Yes           |
| PUT    | /list/{list_id}              |   update the list                     | Yes           |
| DELETE | /list/{list_id}              |   remove the list                     | Yes           |
| DELETE | /list/{list_id}/members      |   remove members from the list        | Yes           |



EXPORT 

| Method | Endpoint             | Description                     | Auth Required |
| ------ | -------------------  | ------------------------------  | ------------- |
| GET    | /export/leads/excel  | Export all leads to Excel file  | Yes           |
| GET    | /export/company/excel| Export all company to Excel file| yes           |

API DOCUMENTATION 
Base URL

http://127.0.0.1:8000



1️⃣ Authentication APIs

Base Path:

/auth
🔹 Signup

POST /signup

Request Body
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "123456"
}
Response
{
  "id": "65f1c9a6...",
  "name": "John Doe",
  "email": "john@example.com"
}
🔹 Login

POST /login

Content-Type:

application/x-www-form-urlencoded
Form Data
username: john@example.com
password: 123456
Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
🔹 Get Current User

GET /me

Headers:

Authorization: Bearer <access_token>
Response
{
  "id": "65f1c9a6...",
  "name": "John Doe",
  "email": "john@example.com"
}
🔹 Logout

POST /logout

Headers:

Authorization: Bearer <access_token>
Response
{
  "message": "Logout successful"
}
2️⃣ User APIs

Base Path:

/users

⚠ Requires Authentication

🔹 Get All Users

GET /users

Response
[
  {
    "id": "65f1c9a6...",
    "name": "John Doe",
    "email": "john@example.com"
  }
]
🔹 Get Single User

GET /users/{id}

🔹 Update User

PUT /users/{id}

Request Body
{
  "name": "Updated Name",
  "email": "updated@email.com"
}
🔹 Delete User

DELETE /users/{id}

3️⃣ Leads APIs

Base Path:

/leads

All routes require:

Authorization: Bearer <token>
🔹 Create Lead (JSON)

POST /leads/create_leads

Form-Data:

lead: {
   "company_name": "ABC Pvt Ltd",
   "vertical": "IT",
   "site_search": ["AI", "Cloud"]
}
🔹 Import Leads (File Upload)

POST /leads/create_leads

Form-Data:

file: upload.csv


🔹 Get All Leads

GET /leads/read_leads

Optional Query Parameters:

?keyword=AI
?vertical=IT
Response
{
  "No of leads": 10,
  "leads": [...]
}

🔹 Get Single Lead

GET /leads/read_leads/{lead_id}

🔹 Update Lead

PUT /leads/update_leads/{lead_id}

🔹 Update Lead Status

PATCH /leads/leads_status/{lead_id}

Request Body
{
  "is_active": true
}



4️⃣ Export API

Base Path:

/export
🔹 Export Leads to Excel

GET /export/leads/excel

Returns:

Excel file download

Content-Type:

application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Authentication Type




GET /export/company/excel

Returns:

Excel file download

Content-Type:

application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Authentication Type

This project uses:

JSON Web Token

Include token in all protected routes:

Authorization: Bearer <access_token>

5 company api

POST /company/create_company 

Form-Data:

company: {
   "company_name": "ABC Pvt Ltd",
   "domain": "IT",
   "keyword": ["AI", "Cloud"]
}
🔹 Import company (File Upload)

Get All  company

GET /company/read_company

Response

 {
        "company_name": "infonet",
        "domain": "software",
        "company_link": "https://www.infosys.com",
        "company_email": "contact@infosys.com",
        "description": "Global IT consulting company",
        "employees_count": 300000,
        "city": "Bangalore",
        "country": "India",
        "links": [],
        "keywords": [],
        "revenue": "18B USD",
        "founded": "1981",
        "contact": "+91-80-2852-0261",
        "owner_id": "699e96b4716f5c474aa51479",
        "created_at": "2026-02-25T06:43:43.475000",
        "added_to_favourites": true,
        "is_active": true,
        "updated_at": "2026-02-25T08:35:17.068000",
        "id": "699e9a1f2fce2bd003d1cac6"
    },

GET /company/read_company/{id}

To get a specific company eg(699e9a1f2fce2bd003d1cac6)
Response
{
   {
        "company_name": "infonet",
        "domain": "software",
        "company_link": "https://www.infosys.com",
        "company_email": "contact@infosys.com",
        "description": "Global IT consulting company",
        "employees_count": 300000,
        "city": "Bangalore",
        "country": "India",
        "links": [],
        "keywords": [],
        "revenue": "18B USD",
        "founded": "1981",
        "contact": "+91-80-2852-0261",
        "owner_id": "699e96b4716f5c474aa51479",
        "created_at": "2026-02-25T06:43:43.475000",
        "added_to_favourites": true,
        "is_active": true,
        "updated_at": "2026-02-25T08:35:17.068000",
        "id": "699e9a1f2fce2bd003d1cac6"
    },
}

To update company 
PUT /update_company/{company_id}

LISTS
1.To create list
Method:POST
body 
for companies list
{
  "list_name": "furniture",
  "description": "interior",
  "type": "companies"
}
for leads list
{
  "list_name": "furniture",
  "description": "interior",
  "type": "people"
}


2.to add members to the specific list

MEthod:POST
for companies 
entity_ids= object_id
Body:
{
  "entity_ids": [
    "69a191bd5ea1c7a4a317356d",
    "69a191bd5ea1c7a4a317356e",
     "69a191be5ea1c7a4a317356f"  
]
}

for people 
entity_ids= object_id

Body
{
  "entity_ids": [
    "69a191c25ea1c7a4a3173577",
    "69a191c25ea1c7a4a3173578",
    "69a191c25ea1c7a4a3173579"
]
} 




📘 Error Responses
400 Bad Request
{
  "detail": "Invalid lead ID format"
}
401 Unauthorized
{
  "detail": "Not authenticated"
}
404 Not Found
{
  "detail": "Lead not found"
} 
