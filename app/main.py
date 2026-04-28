#imports
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from .db import get_connection

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


def render(request: Request, template_name: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


@app.get("/")
def index():
    return RedirectResponse("/decks", status_code=303)


@app.get("/decks")
def list_decks(request: Request):
    with get_connection() as conn:
        decks = conn.execute(
            """
            SELECT id, name, description
            FROM decks
            ORDER BY name
            """
        ).fetchall()

    return render(request, "decks.html", decks=decks)

@app.get("/decks/newest")
def newest_deck(request: Request):
    with get_connection() as conn:
        deck = conn.execute(
            """
            SELECT id, name, description
            FROM decks
            ORDER BY id DESC
            LIMIT 1;
            """
        ).fetchone()

    return render(request, "newest_deck.html", deck=deck)

@app.get("/tags")
def list_tags(request: Request):
    with get_connection() as conn:
        # The SQL query: Select all columns, order by date (newest first)
        tags = conn.execute(
            """
            SELECT name, created_at
            FROM tags
            ORDER BY name
            """
        ).fetchall()

    return render(request, "tags.html", tags=tags)

@app.get("/tags/newest")
def newest_tag(request: Request):
    with get_connection() as conn:
        tag = conn.execute(
            """
            SELECT id, name
            FROM tags
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    return render(request, "newest_tag.html", tag=tag)

@app.post("/tags")
def create_tag(name: str = Form(...)):
    with get_connection() as conn:
        conn.execute(t"""
            INSERT INTO tags (name)
            VALUES ({name})
            """)

    return RedirectResponse("/tags", status_code=303)