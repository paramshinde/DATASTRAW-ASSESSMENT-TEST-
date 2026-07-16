from __future__ import annotations

from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.db import get_connection, init_db, seed_demo_data, ticket_code, transaction, utc_now


BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title="DataStraw Support CRM")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=4000)


class TicketUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(Open|In Progress|Closed)$")
    notes: str | None = Field(default=None, max_length=4000)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_demo_data()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html", {"page_title": "Support CRM"})


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail_page(request: Request, ticket_id: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"page_title": ticket_id, "ticket_id": ticket_id},
    )


@app.post("/api/tickets")
def create_ticket(payload: TicketCreate) -> JSONResponse:
    now = utc_now()
    with transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tickets (
                ticket_id, customer_name, customer_email, subject, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("", payload.customer_name.strip(), payload.customer_email.lower(), payload.subject.strip(), payload.description.strip(), "Open", now, now),
        )
        new_ticket_id = ticket_code(cursor.lastrowid)
        conn.execute("UPDATE tickets SET ticket_id = ? WHERE id = ?", (new_ticket_id, cursor.lastrowid))

    return JSONResponse({"ticket_id": new_ticket_id, "created_at": now}, status_code=201)


@app.get("/api/tickets")
def list_tickets(status: str | None = None, search: str | None = None) -> list[dict]:
    query = """
        SELECT ticket_id, customer_name, subject, status, created_at
        FROM tickets
        WHERE 1 = 1
    """
    params: list[str] = []

    if status and status in {"Open", "In Progress", "Closed"}:
        query += " AND status = ?"
        params.append(status)

    if search:
        term = f"%{search.strip()}%"
        query += """
            AND (
                ticket_id LIKE ?
                OR customer_name LIKE ?
                OR customer_email LIKE ?
                OR subject LIKE ?
                OR description LIKE ?
            )
        """
        params.extend([term, term, term, term, term])

    query += " ORDER BY created_at DESC, ticket_id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict:
    with get_connection() as conn:
        ticket = conn.execute(
            """
            SELECT ticket_id, customer_name, customer_email, subject, description, status, created_at, updated_at
            FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        notes = conn.execute(
            """
            SELECT note_text, created_at
            FROM notes
            WHERE ticket_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (ticket_id,),
        ).fetchall()

    payload = dict(ticket)
    payload["notes"] = [dict(note) for note in notes]
    return payload


@app.put("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: str, payload: TicketUpdate = Body(...)) -> dict[str, object]:
    with transaction() as conn:
        ticket = conn.execute(
            "SELECT ticket_id FROM tickets WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        updated_at = utc_now()
        updates: list[str] = []
        params: list[str] = []

        if payload.status:
            updates.append("status = ?")
            params.append(payload.status)

        if updates:
            updates.append("updated_at = ?")
            params.append(updated_at)
            params.append(ticket_id)
            conn.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE ticket_id = ?", params)

        if payload.notes and payload.notes.strip():
            conn.execute(
                "INSERT INTO notes (ticket_id, note_text, created_at) VALUES (?, ?, ?)",
                (ticket_id, payload.notes.strip(), updated_at),
            )
            conn.execute(
                "UPDATE tickets SET updated_at = ? WHERE ticket_id = ?",
                (updated_at, ticket_id),
            )

    return {"success": True, "updated_at": updated_at}


@app.exception_handler(HTTPException)
def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
