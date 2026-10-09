# EventMate AI — College Event Chatbot (Python)

A Flask + SQLite college project with a chatbot, event calendar, student registrations, and admin dashboard.

## Features
- Chatbot answers from event data stored in SQLite
- Event dates, times, venues, eligibility, and registration deadlines
- Student event registration; prevents duplicate registration by email per event
- Admin login, add/delete events, and view registrations
- Database and sample events are created automatically

## Requirements
Python 3.10+ and pip.

## Windows setup
1. Extract the ZIP file.
2. Open PowerShell in the extracted `college_event_ai_chatbot` folder.
3. Run:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   python app.py
   ```
4. Open http://127.0.0.1:5000

## macOS/Linux setup
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Admin demo login
- URL: http://127.0.0.1:5000/admin/login
- Username: `admin`
- Password: `admin123`

Change the credentials and `SECRET_KEY` environment variable before any deployment. Never use Flask's development server for production.

## Try these chatbot questions
- Show upcoming events
- When is CodeSprint Challenge?
- Where is the AI workshop?
- How do I register?
- How do I get a certificate?

## Important
The included chatbot uses local keyword matching and the SQLite event database. It needs no AI API key, but it is a chatbot prototype rather than a large-language-model-powered assistant. Connect an approved AI API inside `answer()` if you want more flexible natural-language answers. Sample events are fictional demo data: replace them with confirmed college details. Do not use real sensitive student data in this demo.
