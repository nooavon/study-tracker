from fastapi import FastAPI, Request
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