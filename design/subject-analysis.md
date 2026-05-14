# Study tracker — domain reading (three-pass)

**Purpose:** This note reads the repository as a case description: what the domain *is* (entities and links), what users can *do* (actions and implied rules), and what a production system would still need to decide (open questions).

**Package convention:** Unless a sentence is labeled **Proposal** or points to [design-rationale.md](design-rationale.md) / [er-diagram.md](er-diagram.md) for proposed extensions, this note **describes the project as it exists in the repo** (migrations and routes), not a future product.

---

## Pass 1 — Candidate entities and relationships

**Domain entities** (five tables in the flashcard vocabulary; each maps to a box in [er-diagram.md](er-diagram.md)):

- **Deck** — A named collection of flashcards. Has a required unique name, optional description, and creation time.
- **Card** — A question–answer item that belongs to exactly one deck, with its own creation time.
- **Tag** — A reusable label; has a name and creation time. Not scoped to a deck or user in the schema.
- **Card tag (association)** — Links one card to one tag; the pair is unique (composite primary key). **Terminology:** the physical table is `card_tags`; the ER diagram labels the same structure **CardTag**.
- **Review** — A numeric rating (1–5) on a single card, with a timestamp of when it was recorded. The physical table is `reviews`. There is no `user_id` on a review: attribution to a specific learner is not represented (accepted limitation for this teaching schema).

**Roles** (behavioral actors, **not** drawn as entities in the flashcard ER diagram):

- **Learner** — The person using the app; there is no `user_id` or account model, so “who owns this deck?” is not represented.
- **System** — Applies schema changes and records which migration files ran (`schema_migrations` in [app/migrate.py](../app/migrate.py)); operational bookkeeping, **out of scope** for the content ER diagram in [er-diagram.md](er-diagram.md).

**Relationships** (foreign keys and how they read in the domain):

- **Deck contains many cards** — Every card points at one deck; deleting a deck is defined to cascade removal of its cards at the database level.
- **Card has many tags; tag applies to many cards** — Many-to-many through the card–tag association table, keyed by card and tag identifiers.
- **Card has many reviews; each review belongs to exactly one card** — Every review row references one `cards.id` with `ON DELETE CASCADE`, so deleting a card removes its reviews; when a deck is deleted and its cards cascade away, those cards’ reviews go with them.

---

## Pass 2 — Actions, connections, and rules

**Actions**:

- **Decks:** List decks; create a deck; delete a deck; open the most recently created deck (by id); open a deck and see its cards; add a card to a deck; edit a deck’s name and description.
- **Tags:** List tags; create a tag; open the newest tag; edit or delete a tag.
- **Cards:** Open a card’s detail (see deck context, tags on the card, and tags not yet on the card); add an existing tag to that card.
- **Reviews:** The schema supports storing ratings over time on cards (`reviews` table). There are no routes in the teaching app to create, list, or edit reviews; persistence is for data-model and query exercises (same pattern as cross-deck tag search: relationships exist, UI does not).

**Connections**:

- Card **inner join** deck — Card detail always loads the parent deck’s id and name.
- Card tags **inner join** tag — Resolves tag ids to names for display on a card.
- Tags **filtered with not exists** — Produces “available” tags for the add-tag control without duplicating links already present.

**Rules**:

1. **A new deck must have a name**; description may be omitted.
2. **A new card must have both a question and an answer** (both required on submit).
3. **Linking the same tag to the same card again is a no-op** — The insert uses conflict handling so duplicate associations do not surface as errors.
4. **There is no authorization layer** — Any client that can reach the app can create, update, or delete domain data; ownership and auditing are not enforced in route logic.
5. **Review ratings are integers from 1 to 5 inclusive** — Enforced with a `CHECK` constraint on `reviews.rating` in migrations.
6. **Review history is retained** — Rows are not expired or summarized by the schema; retention policy is “keep forever” for now.
7. **Reviews are anonymous at the schema level** — No foreign key to a user or learner table on `reviews`.

## Pass 3 — Open questions

1. **User** — The schema has no `user_id`. Is that intended, or a shortcut?

2. **Tag names vs deck names** — Deck names are unique in the database; tag names are not. Should uniqueness be enforced and how should conflicts be shown in the UI?

3. **Card lifecycle vs deck/tag lifecycle** — Decks and tags support edit and delete flows; cards can be created and viewed and tagged, but not edited, deleted, or untagged via routes. Is the card model intentionally minimal, or incomplete?

4. **Deleting decks when cards have tags** — Cards cascade from deck deletion, but associations from cards to tags use default referential rules. In a real deployment, can deleting a deck with tagged cards fail or leave orphans? Should association rows cascade when a card is removed?

5. **Query construction discipline** — Tag lookup by id builds the `WHERE` clause with string interpolation instead of a bound parameter. That is safe only while the route always supplies a typed integer; should production code standardize on parameters everywhere?

### Status of open questions

| # | Question | Where it stands |
|---|----------|-----------------|
| 1 | User / `user_id` | **Addressed in [design-rationale.md](design-rationale.md):** as-built, no user table; **Proposal** there = `User` (or external identity) plus ownership FKs, aligned with `†` in [er-diagram.md](er-diagram.md). |
| 2 | Tag vs deck name uniqueness | **Left open** for product/UI (how to show conflicts). **Proposal** in rationale/diagram: per-owner tag uniqueness if accounts exist; deck name uniqueness scope may shift from global to per owner. |
| 3 | Card lifecycle vs deck/tag | **Left open** (minimal teaching surface vs incomplete product). Mentioned as route-level gap in rationale. |
| 4 | Deck delete and `card_tags` | **Reconstructed risk** in note and diagram; **Proposal** in rationale/diagram = explicit `ON DELETE` rules (e.g. cascade link rows with cards). |
| 5 | Query parameterization | **Not an ER issue.** **Left open** as team standard; **Proposal** in rationale = always use bound parameters in application SQL. |

### Resolved choices for reviews (recorded for the package)

These are product decisions taken for the current teaching model; they are not numbered with the open questions above.

| Topic | Decision |
|-------|----------|
| Retention | Keep review history indefinitely (no archival or TTL in schema). |
| Rating scale | Numeric 1–5 inclusive, enforced in the database. |
| Delete behavior | `reviews.card_id` uses `ON DELETE CASCADE` with `cards`. |
| Attribution | No per-user column on `reviews`; fine-grained “who rated” is out of scope. |

---

## Likely application queries

How each query maps onto the ER model is spelled out under **Testing the design against these queries** in [er-diagram.md](er-diagram.md).

| Query | Status in this project |
|-------|-------------------------|
| List all decks sorted alphabetically by name | **Implemented** (deck index). |
| Load the newest deck | **Implemented** (newest deck route uses `ORDER BY id DESC LIMIT 1`). |
| Find all cards (across decks) that carry a given tag, for study or navigation | **Not implemented** — Tags are browsed and attached per card, but there is no cross-deck “study by tag” or search view. |
| How many reviews has each card received? | **Not implemented** in routes — Supported by **Card → Review** (`COUNT` grouped by `card_id`). |
| What is the most recent review for a given card? | **Not implemented** in routes — Supported by filtering `reviews` to one `card_id` and ordering by `reviewed_at` (or `MAX(reviewed_at)`). |
| What is the average rating per deck? | **Not implemented** in routes — Supported by **Deck → Card → Review** with `AVG(rating)` grouped by deck. |
| Which cards have not been reviewed yet? | **Not implemented** in routes — Supported by **Card** `LEFT JOIN` **Review** with `WHERE reviews.id IS NULL` (or `NOT EXISTS`). |
