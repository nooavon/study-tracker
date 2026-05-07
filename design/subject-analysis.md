# Study tracker — domain reading (three-pass)

**Purpose:** This note reads the repository as a case description: what the domain *is* (entities and links), what users can *do* (actions and implied rules), and what a production system would still need to decide (open questions).

---

## Pass 1 — Candidate entities and relationships

**Entities** (each table in migrations is a candidate aggregate or value in the domain):

- **Deck** — A named collection of flashcards. Has a required unique name, optional description, and creation time.
- **Card** — A question–answer item that belongs to exactly one deck, with its own creation time.
- **Tag** — A reusable label; has a name and creation time. Not scoped to a deck or user in the schema.
- **Card tag (association)** — Links one card to one tag; the pair is unique (composite primary key).

**Relationships** (foreign keys and how they read in the domain):

- **Deck contains many cards** — Every card points at one deck; deleting a deck is defined to cascade removal of its cards at the database level.
- **Card has many tags; tag applies to many cards** — Many-to-many through the card–tag association table, keyed by card and tag identifiers.

**Roles** (implied, not stored):

- **Learner** — The person using the app; there is no `user_id` or account model, so “who owns this deck?” is not represented.
- **System** — Applies schema changes and records which migration files ran (operational bookkeeping, not part of the flashcard vocabulary).

---

## Pass 2 — Actions, connections, and rules

**Actions**:

- **Decks:** List decks; create a deck; delete a deck; open the most recently created deck (by id); open a deck and see its cards; add a card to a deck; edit a deck’s name and description.
- **Tags:** List tags; create a tag; open the newest tag; edit or delete a tag.
- **Cards:** Open a card’s detail (see deck context, tags on the card, and tags not yet on the card); add an existing tag to that card.

**Connections**:

- Card **inner join** deck — Card detail always loads the parent deck’s id and name.
- Card tags **inner join** tag — Resolves tag ids to names for display on a card.
- Tags **filtered with not exists** Produces “available” tags for the add-tag control without duplicating links already present.

**Rules**:

1. **A new deck must have a name**; description may be omitted.
2. **A new card must have both a question and an answer** (both required on submit).
3. **Linking the same tag to the same card again is a no-op** — The insert uses conflict handling so duplicate associations do not surface as errors.
4. **There is no authorization layer** — Any client that can reach the app can create, update, or delete domain data; ownership and auditing are not enforced in route logic.

## Pass 3 — Open questions

1. **User** — The schema has no `user_id`. is that intended, or a shortcut?

2. **Tag names vs deck names** — Deck names are unique in the database; tag names are not. Should uniqueness be enforced and how should conflicts be shown in the UI?

3. **Card lifecycle vs deck/tag lifecycle** — Decks and tags support edit and delete flows; cards can be created and viewed and tagged, but not edited, deleted, or untagged via routes. Is the card model intentionally minimal, or incomplete?

4. **Deleting decks when cards have tags** — Cards cascade from deck deletion, but associations from cards to tags use default referential rules. In a real deployment, can deleting a deck with tagged cards fail or leave orphans? Should association rows cascade when a card is removed?

5. **Query construction discipline** — Tag lookup by id builds the `WHERE` clause with string interpolation instead of a bound parameter. That is safe only while the route always supplies a typed integer; should production code standardize on parameters everywhere?

---

## Likely application queries

| Query | Status in this project |

| List all decks sorted alphabetically by name | **Implemented** (deck index). |
| Load the newest deck. | **Implemented** (Newest deck). |
| Find all cards (across decks) that carry a given tag, for study or navigation | **Not implemented** — Tags are browsed and attached per card, but there is no cross-deck “study by tag” or search view. |