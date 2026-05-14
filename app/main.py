from .queries.tags import fetch_all_tags, fetch_newest_tag, fetch_tag_by_id, insert_tag, update_tag, delete_tag
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
            "SELECT id, name, description FROM decks ORDER BY name"
        ).fetchall()
    return render(request, "decks.html", decks=decks)


@app.post("/decks")
def create_deck(name: str = Form(...), description: str = Form(None)):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO decks (name, description) VALUES (%s, %s)",
            (name, description),
        )
    return RedirectResponse("/decks", status_code=303)


@app.post("/decks/{deck_id}/delete")
def delete_deck(deck_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
    return RedirectResponse("/decks", status_code=303)


@app.get("/decks/newest")
def newest_deck(request: Request):
    with get_connection() as conn:
        deck = conn.execute(
            "SELECT id, name, description FROM decks ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return render(request, "newest_deck.html", deck=deck)


@app.get("/decks/{deck_id}")
def get_deck(request: Request, deck_id: int):
    with get_connection() as conn:
        deck = conn.execute(
            "SELECT id, name, description FROM decks WHERE id = %s",
            (deck_id,),
        ).fetchone()
        cards = conn.execute(
            """
            SELECT
              c.id,
              c.question,
              c.answer,
              COUNT(r.id) AS review_count,
              ROUND(AVG(r.rating)::numeric, 1) AS average_rating
            FROM cards AS c
            LEFT JOIN reviews AS r ON r.card_id = c.id
            WHERE c.deck_id = %s
            GROUP BY c.id, c.question, c.answer, c.created_at
            ORDER BY c.created_at ASC, c.id
            """,
            (deck_id,),
        ).fetchall()
    return render(request, "deck_detail.html", deck=deck, cards=cards)

@app.post("/decks/{deck_id}/cards")
def create_card(deck_id: int, question: str = Form(...), answer: str = Form(...)):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO cards (deck_id, question, answer) VALUES (%s, %s, %s)",
            (deck_id, question, answer),
        )
    return RedirectResponse(f"/decks/{deck_id}", status_code=303)


@app.get("/decks/{deck_id}/edit")
def edit_deck_route(request: Request, deck_id: int):
    with get_connection() as conn:
        deck = conn.execute(
            "SELECT id, name, description FROM decks WHERE id = %s", 
            (deck_id,)
        ).fetchone()
    return render(request, "deck_edit.html", deck=deck)

@app.post("/decks/{deck_id}/edit")
def update_deck_route(deck_id: int, name: str = Form(...), description: str = Form(None)):
    with get_connection() as conn:
        conn.execute(
            "UPDATE decks SET name = %s, description = %s WHERE id = %s",
            (name, description, deck_id)
        )
    return RedirectResponse("/decks", status_code=303)

@app.get("/tags")
def list_tags_route(request: Request): 
    with get_connection() as conn:
        tags = fetch_all_tags(conn)
    return render(request, "tags.html", tags=tags)

@app.get("/tags/newest")
def newest_tag_route(request: Request): 
    with get_connection() as conn:
        tag = fetch_newest_tag(conn)
    return render(request, "newest_tag.html", tag=tag)

@app.get("/tags/{tag_id}/edit")
def edit_tag_route(request: Request, tag_id: int):
    with get_connection() as conn:
        tag = fetch_tag_by_id(conn, tag_id)
    return render(request, "tag_edit.html", tag=tag)

@app.post("/tags")
def create_tag_route(name: str = Form(...)): 
    with get_connection() as conn:
        insert_tag(conn, name)
    return RedirectResponse("/tags", status_code=303)

@app.post("/tags/{tag_id}/edit")
def update_tag_route(tag_id: int, name: str = Form(...)): 
    with get_connection() as conn:
        update_tag(conn, tag_id, name)
    return RedirectResponse("/tags", status_code=303)

@app.post("/tags/{tag_id}/delete")
def delete_tag_route(tag_id: int): 
    with get_connection() as conn:
        delete_tag(conn, tag_id) 
    return RedirectResponse("/tags", status_code=303)

@app.get("/cards/{card_id}")
def show_card(request: Request, card_id: int):
    with get_connection() as conn:
        card = conn.execute(
            """
            SELECT
              c.id,
              c.question,
              c.answer,
              d.id AS deck_id,
              d.name AS deck_name
            FROM cards AS c
            INNER JOIN decks AS d ON d.id = c.deck_id
            WHERE c.id = %s
            """,
            (card_id,),
        ).fetchone()

        if card is None:
            return RedirectResponse("/decks", status_code=303)

        tags = conn.execute(
            """
            SELECT
              t.id,
              t.name
            FROM card_tags AS ct
            INNER JOIN tags AS t ON t.id = ct.tag_id
            WHERE ct.card_id = %s
            ORDER BY t.name
            """,
            (card_id,),
        ).fetchall()

        available_tags = conn.execute(
            """
            SELECT
              t.id,
              t.name
            FROM tags AS t
            WHERE NOT EXISTS (
              SELECT 1
              FROM card_tags AS ct
              WHERE ct.card_id = %s
                AND ct.tag_id = t.id
            )
            ORDER BY t.name
            """,
            (card_id,),
        ).fetchall()

    return render(
        request,
        "card_detail.html",
        card=card,
        tags=tags,
        available_tags=available_tags,
    )

@app.post("/cards/{card_id}/tags")
def add_tag_to_card(card_id: int, tag_id: int = Form(...)):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO card_tags (card_id, tag_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (card_id, tag_id),
        )

    return RedirectResponse(f"/cards/{card_id}", status_code=303)


@app.post("/cards/{card_id}/reviews")
def create_review(card_id: int, rating: int = Form(...)):
    with get_connection() as conn:
        card = conn.execute(
            "SELECT deck_id FROM cards WHERE id = %s",
            (card_id,),
        ).fetchone()

        if card is None:
            return RedirectResponse("/decks", status_code=303)

        conn.execute(
            "INSERT INTO reviews (card_id, rating) VALUES (%s, %s)",
            (card_id, rating),
        )

    return RedirectResponse(f"/decks/{card['deck_id']}", status_code=303)