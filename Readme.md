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

######  Project Structure
crm_backend/ -->
│
├── main.py
├── database.py
├── Api/
│     ├── leads.py
│     └── user.py
│
├── Auth/
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
│     └── leads_service.py
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
| PATCH  | /leads/leads_status/{id} | Activate/Deactivate a lead       | Yes           |


EXPORT 

| Method | Endpoint            | Description                    | Auth Required |
| ------ | ------------------- | ------------------------------ | ------------- |
| GET    | /export/leads/excel | Export all leads to Excel file | Yes           |



API DOCUMENTATION 
Base URL

http://127.0.0.1:8000
1️⃣ Authentication APIs

Base Path:

/auth
🔹 Signup

POST /auth/signup

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

POST /auth/login

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

GET /auth/me

Headers:

Authorization: Bearer <access_token>
Response
{
  "id": "65f1c9a6...",
  "name": "John Doe",
  "email": "john@example.com"
}
🔹 Logout

POST /auth/logout

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

This project uses:

JSON Web Token

Include token in all protected routes:

Authorization: Bearer <access_token>

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
