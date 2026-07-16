# DataStraw Support CRM

A full-stack customer support ticketing CRM built for the DataStraw assessment with:

- FastAPI backend
- SQLite database
- HTML + Tailwind frontend
- Live ticket search, filtering, detail views, status updates, and notes

## Features

- Create support tickets with customer details and issue description
- List tickets with status and timestamp
- Search across ticket ID, customer name, email, subject, and description
- Filter by ticket status
- View individual ticket details
- Update status and add notes/comments

## Tech Stack

- Python 3
- FastAPI
- SQLite
- Jinja2 templates
- Tailwind CSS via CDN

## Local Setup

1. Create a virtual environment if you want one.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the environment file:

```bash
cp .env.example .env
```

4. Run the server:

```bash
uvicorn app.main:app --reload
```

5. Open the app:

```text
http://127.0.0.1:8000
```

## API

- `POST /api/tickets`
- `GET /api/tickets`
- `GET /api/tickets/{ticket_id}`
- `PUT /api/tickets/{ticket_id}`

## Deployment Notes

This app is ready for Railway deployment as a standard FastAPI service. Use:

- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Demo Data

The first startup seeds a few sample tickets so the UI is not empty on launch.

