# Design rationale — study tracker

This document explains **why** the domain is shaped the way it is. [subject-analysis.md](subject-analysis.md) reconstructs what the teaching app does; [er-diagram.md](er-diagram.md) shows entities and relationships. Here we separate **intent read from the existing code** from **proposals a production version would still need**, so a reader does not mistake pedagogy for product policy.

**Package convention:** A paragraph labeled *Reconstructed from code* (or *Reconstructed from app*) states what the repo does today. A paragraph labeled *Proposal* describes a direction a real product might take but that is **not** asserted as current behavior. *Left open* marks a product choice the documents do not resolve.

---

## Status of open questions (from [subject-analysis.md](subject-analysis.md))

| # | Topic | Resolution in this package |
|---|--------|----------------------------|
| 1 | User / `user_id` | *Reconstructed:* no user table in migrations. *Proposal:* add **User** (or external identity) and ownership FKs on **Deck** / **Tag**, as in `†` on [er-diagram.md](er-diagram.md). |
| 2 | Tag vs deck name uniqueness | *Left open* for UX (how to show duplicate or conflict errors). *Proposal:* if accounts exist, scope tag name uniqueness per owner; deck names may move from **global** unique to **per-owner** unique—see identifiers below. |
| 3 | Card lifecycle vs deck/tag | *Left open* whether minimal routes are intentional. *Reconstructed gap:* no edit/delete/untag card in the teaching surface. |
| 4 | Deck delete vs `card_tags` | *Reconstructed risk:* default FK behavior on `card_tags` may interact badly with cascading card deletes. *Proposal:* explicit `ON DELETE` (e.g. cascade link rows with cards), as noted in [er-diagram.md](er-diagram.md). |
| 5 | SQL parameterization | *Reconstructed:* one tag query path uses string interpolation for an id. *Not an ER topic.* *Proposal:* bind all parameters; *left open* as a coding-standard decision. See [SQL construction](#sql-construction-implementation-not-er) below. |

---

## Identifiers for the main entities

**Deck** — *Reconstructed from code:* the table `decks` uses a surrogate `id` (`SERIAL`) and a human-facing `name` with a **global** uniqueness constraint. That pattern is a reasonable default for a small app: stable join keys and simple URLs (`/decks/{deck_id}`). *Proposal:* if accounts exist, **keep** surrogate `id` for joins and bookmarks, but **change** uniqueness so `name` is unique **per owner** (not globally), matching how people actually name decks (“Biology”) without colliding across tenants.

**Card** — *Reconstructed from code:* `cards.id` is the same surrogate style; `deck_id` ties each card to exactly one deck. *Proposal:* retain `id` and `deck_id` in a typical production model—they match the mental model and the routes. *Optional change:* expose opaque public ids (UUIDs) in APIs if you want non-guessable URLs; that is an implementation preference, not a domain correction.

**Tag** — *Reconstructed from code:* `tags.id` plus string `name`, with **no** uniqueness on `name`. The identifier story is “internal id for joins, string for display.” *Proposal:* **keep** `id`; **add** either scoped uniqueness `(owner_id, name)` or a separate slug field if tags become shareable or API-addressable—today duplicate names are possible and ambiguous in the UI.

**Card tag (association)** — *Reconstructed from code:* the table `card_tags` uses the composite identity `(card_id, tag_id)` as primary key—no separate surrogate. *Proposal:* **keep** that design: the pair *is* the logical identifier of “this tag on this card.” *Optional addition (proposal):* a column such as `linked_at` if the product cares about *when* the link was created (ordering, audit, analytics); the teaching schema omits it.

**Review** — *Reconstructed from migrations:* the table `reviews` stores **append-only rating events** on a card: surrogate `id`, required `card_id`, integer `rating` constrained to **1–5** inclusive, and `reviewed_at` defaulting to insert time. **Why under `cards`:** a review always targets one flashcard; deck-level averages and counts are **derived** by joining **Deck → Card → Review**, which matches “how hard was this item?” better than a single deck-level score with no card anchor. **Why `ON DELETE CASCADE` on `card_id`:** when a card disappears (including because its deck was deleted and cards cascaded), dependent review rows must not outlive the card—no orphan ratings. **Why a `CHECK` on `rating`:** keeps invalid scores out of the database regardless of application bugs; the UI contract stays simple. **Why no `user_id`:** the teaching schema deliberately avoids tying ratings to an account; *proposal:* add `reviewer_user_id` (or opaque subject id) if the product needs attribution, leaderboards, or abuse investigation.

**User** — *Not in the project; proposal:* a `users` table (or external identity provider subject) with surrogate `id` is the usual anchor for ownership and access control. Natural keys like email are poor primary keys (they change); **prefer** surrogate `id` plus unique email/login where needed.

---

## Many-to-many: why `card_tags` is its own structure

*Reconstructed from code:* **Card** and **Tag** are independent lifecycles: a tag can label many cards, and a card can carry many tags. That is a textbook many-to-many. The project models it with **`card_tags`**, an associative entity, rather than encoding tag lists inside `cards` or duplicating tag rows per card.

**Reason it is modeled this way:** normalized storage, referential integrity (a link always points at real `cards` and `tags` rows), and a clear place for **relationship-only** facts later—e.g. when the tag was applied (*proposal*, not in migrations). A JSON array of tag names on `cards` would dodge a table but would weaken integrity and make queries like “all cards with tag X” harder. The teaching project chose the structure a real database-backed app would keep.

### Design hygiene (anti-patterns avoided)

*Reconstructed from code:* the schema does **not** store multiple tags as a **comma-separated list** (or other undelimited string) on `cards`, does **not** use **repeating groups** of tag columns on a single card row, and does **not** collapse decks, cards, tags, and links into one **god table**. One row per card, one row per link in `card_tags`, and separate tables per entity follow normalization and keep integrity enforceable—consistent with common “patterns vs anti-patterns” guidance for relational designs.

---

## SQL construction (implementation, not ER)

*Reconstructed from code:* tag lookup by primary key in [app/queries/tags.py](../app/queries/tags.py) builds the `WHERE` clause with string interpolation instead of a bound parameter; the route currently supplies a typed integer, which limits immediate risk.

*Proposal:* production code should **always** use bound parameters for dynamic SQL. *Left open:* whether this is enforced by linter, review checklist, or ORM-only access—no migration or ER change is required to adopt the habit.

---

## Privacy and data minimization (proposal)

*Reconstructed from code:* the teaching app stores **no** user accounts and imposes **no** access rules, so it has nothing to minimize yet. The schema **does** persist **`reviews.reviewed_at`**: timestamps are coarse compared to full session logs, but they still allow “this card was rated at time *t*” without naming *who* rated it.

*Proposal:* a real version should decide explicitly what **not** to persist and what **must** be gated. Do **not** store long-lived **raw IP addresses or full request payloads** tied to study content unless there is a documented need (abuse prevention, legal hold); if logs are required, prefer short retention, aggregation, or hashed identifiers. **Access rule:** every read and write on `decks`, `cards`, `tags`, `card_tags`, and `reviews` should be authorized against an authenticated principal (e.g. “only the owner—or explicitly shared viewers—may read this deck”). That rule is absent today; adding it is as much a product decision as a schema decision.

---

## Decisions a real version must make (silently skipped today)

1. **Tenancy and ownership** — *Reconstructed:* the schema has no `user_id`. *Proposal / left open:* introduce a **`users`** (or workspace) model and foreign keys from `decks` and likely `tags`, or deliberately build a single-tenant, trust-boundary tool (e.g. desktop-only, no server). The code does not say which was intended; a product must choose.

2. **Audit and lifecycle metadata** — *Reconstructed:* cards, decks, and tags have `created_at`; review rows carry **`reviewed_at`** for when each rating was stored. There are **no** `updated_at`, **no** “who changed this,” and **no** soft-delete flags on those entities. *Proposal:* a real system usually needs at least **update timestamps and actor** for support and compliance, or a conscious decision to stay minimal.

3. **Referential cleanup** — *Reconstructed:* `cards` cascade when a deck is deleted; `card_tags` uses default FK behavior. *Proposal:* specify **ON DELETE** rules on `card_tags` so deck or card removal does not fail or leave orphans.

Additional gap (*reconstructed from routes*): asymmetric **card** maintenance—create and tag, but no edit/delete card in the teaching surface—so product policy for card lifecycle is *left open*.

---

## ER diagram: non-obvious choices explained here

The Mermaid figure in [er-diagram.md](er-diagram.md) is a **union** (as-built + `†`). The following are easy to misread without this cross-reference:

- **`User` and edges `owns` / `defines`** — *Proposal only.* The repo has neither table nor FKs; they encode the analyst’s answer to “where would ownership live?”
- **`Deck.name` shown with UK** — *As-built:* reflects the real **global** `UNIQUE` on `decks.name`. If **User** is added (*proposal*), the meaningful rule usually becomes unique name **per owner**, not globally; the attributes table in the diagram states that shift.
- **`CardTag.linked_at`** — *Proposal only;* not in `card_tags` today.
- **Many-to-many drawn as CardTag** — *Reconstructed:* matches table `card_tags`; the diagram name **CardTag** is labeling only.
- **`Review` and `Card ||--o{ Review`** — *As-built:* matches table `reviews` and the one-to-many from **Card**; not a proposal box.

---

## Open question with more than one defensible answer

**Should “study sessions” be a first-class header entity?** (Distinct from per-card **Review** rows, which are now in the teaching schema.)

*Reconstructed from migrations:* **`reviews`** implements **append-only per-card rating events** with `reviewed_at`—the “middle path” described in earlier drafts (metrics from events without a mandatory session row). There is still **no** `study_sessions` table.

- **One defensible answer: stop at `reviews`** — Enough for counts, averages, recency, and “never reviewed” cards at the SQL layer; the teaching app does not yet expose review CRUD in routes.

- **Another defensible answer: add `study_session` (or equivalent)** — If the product needs a bounded study interval (start/end, mode, device), a header row plus optional links to review events can reduce ambiguity and support UX like “resume where you left off.”

- **Privacy tie-in:** fine-grained timestamps on reviews (and even more so on sessions) deserve an explicit retention and attribution policy once identities exist.

*Left open* whether a session entity is worth the complexity for this codebase; **`reviews`** no longer “stay silent” in migrations, but **session** structure still does.

---

## What remains open to redesign

Nothing in the teaching schema is sacred for a real product. **`card_tags`** might gain relationship attributes or stricter delete rules; **`tags`** might become user-scoped, shared across a workspace, or a global curated taxonomy; **`decks` / `cards`** might split into “library” vs “instance” if content is reused; **`reviews`** might gain a reviewer FK, soft-delete, or archival partitions; a **`users`** table might be replaced by “bring your own identity” with only opaque subject ids. Those forks are **not** prescribed here—only the distinction matters: **reconstruct what the repo does**, then **argue what a serious deployment would still need to decide**.

---

## Dashboard aggregates (as-built)

*Reconstructed from code:* `GET /dashboard` answers “how much content exists?” and “what happened lately?” without changing the schema.

- **Global totals** — Four simple `COUNT` / `AVG` queries over `decks`, `cards`, and `reviews` (overall average uses `COALESCE` so an empty `reviews` table shows **0**, not null).
- **Per-deck rows** — All decks are listed from `decks ORDER BY name`. Card counts and review counts come from **two separate** grouped queries (`cards GROUP BY deck_id`, and `cards` joined to `reviews` grouped by `deck_id`). The route builds a dict per `deck_id` and defaults missing keys to **0**, so a deck with no cards or no reviews still appears with honest zeros rather than being dropped by an inner join.
- **Recent activity** — The ten latest `reviews` rows, ordered by `reviewed_at DESC`, joined to **Card** and **Deck** for display labels. An empty list renders **No reviews yet.**

*Left open for a production fork:* per-deck **average** rating on the dashboard, filtering by date range, and pagination beyond ten events.

---

## Reading this with the diagram

Together, [er-diagram.md](er-diagram.md) and this note mean: **solid lines and tables marked `*`** are the teaching database as shipped (**Deck**, **Card**, **Tag**, **CardTag**, **Review**); **† elements** (User, ownership, `linked_at`, per-owner uniqueness) are **analyst proposals** for a multi-user, production-shaped evolution—not bugs in the assignment. Anyone merging the two documents should see both **what exists** and **what still requires an explicit decision**.