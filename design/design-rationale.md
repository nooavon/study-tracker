# Design rationale — study tracker

This document explains **why** the domain is shaped the way it is. [subject-analysis.md](subject-analysis.md) reconstructs what the teaching app does; [er-diagram.md](er-diagram.md) shows entities and relationships. Here we separate **intent read from the existing code** from **proposals a production version would still need**, so a reader does not mistake pedagogy for product policy.

---

## Identifiers for the main entities

**Deck** — *Reconstructed from code:* the table `decks` uses a surrogate `id` (`SERIAL`) and a human-facing `name` with a **global** uniqueness constraint. That pattern is a reasonable default for a small app: stable join keys and simple URLs (`/decks/{deck_id}`). *Proposal:* if accounts exist, **keep** surrogate `id` for joins and bookmarks, but **change** uniqueness so `name` is unique **per owner** (not globally), matching how people actually name decks (“Biology”) without colliding across tenants.

**Card** — *Reconstructed:* `cards.id` is the same surrogate style; `deck_id` ties each card to exactly one deck. *Keep* `id` and `deck_id` in a real version—they match the mental model and the routes. *Optional change:* expose opaque public ids (UUIDs) in APIs if you want non-guessable URLs; that is an implementation preference, not a domain correction.

**Tag** — *Reconstructed:* `tags.id` plus string `name`, with **no** uniqueness on `name`. The identifier story is “internal id for joins, string for display.” *Proposal:* **keep** `id`; **add** either scoped uniqueness `(owner_id, name)` or a separate slug field if tags become shareable or API-addressable—today duplicate names are possible and ambiguous in the UI.

**Card tag (association)** — *Reconstructed:* the table `card_tags` uses the composite identity `(card_id, tag_id)` as primary key—no separate surrogate. *Keep* that design: the pair *is* the logical identifier of “this tag on this card.” *Optional addition (proposal):* a column such as `linked_at` if the product cares about *when* the link was created (ordering, audit, analytics); the teaching schema omits it.

**User** — *Not in the project; analyst proposal:* a `users` table (or external identity provider subject) with surrogate `id` is the usual anchor for ownership and access control. Natural keys like email are poor primary keys (they change); **prefer** surrogate `id` plus unique email/login where needed.

---

## Many-to-many: why `card_tags` is its own structure

*Reconstructed from code:* **Card** and **Tag** are independent lifecycles: a tag can label many cards, and a card can carry many tags. That is a textbook many-to-many. The project models it with **`card_tags`**, an associative entity, rather than encoding tag lists inside `cards` or duplicating tag rows per card.

**Reason it is modeled this way:** normalized storage, referential integrity (a link always points at real `cards` and `tags` rows), and a clear place for **relationship-only** facts later—e.g. when the tag was applied (*proposal*, not in migrations). A JSON array of tag names on `cards` would dodge a table but would weaken integrity and make queries like “all cards with tag X” harder. The teaching project chose the structure a real database-backed app would keep.

---

## Privacy and data minimization (proposal)

The teaching app stores **no** user accounts and imposes **no** access rules, so it has nothing to minimize yet. A real version should decide explicitly what **not** to persist and what **must** be gated.

**Proposal — minimize and gate:** do **not** store long-lived **raw IP addresses or full request payloads** tied to study content unless there is a documented need (abuse prevention, legal hold); if logs are required, prefer short retention, aggregation, or hashed identifiers. **Access rule:** every read and write on `decks`, `cards`, `tags`, and `card_tags` should be authorized against an authenticated principal (e.g. “only the owner—or explicitly shared viewers—may read this deck”). That rule is absent today; adding it is as much a product decision as a schema decision.

---

## Decisions a real version must make (silently skipped today)

1. **Tenancy and ownership** — The schema has no `user_id`. Either introduce a **`users`** (or workspace) model and foreign keys from `decks` and likely `tags`, or deliberately build a single-tenant, trust-boundary tool (e.g. desktop-only, no server). The code does not say which was intended; a product must choose.

2. **Audit and lifecycle metadata** — Cards have `created_at`; decks and tags do too. There are **no** `updated_at`, **no** “who changed this,” and **no** soft-delete flags. A real system usually needs at least **update timestamps and actor** for support and compliance, or a conscious decision to stay minimal.

3. **Referential cleanup** — `cards` cascade when a deck is deleted; `card_tags` uses default FK behavior. A real version should specify **ON DELETE** rules on `card_tags` so deck or card removal does not fail or leave orphans (*reconstructed gap* from subject analysis).

*(Additional gap, visible in routes rather than schema: asymmetric **card** maintenance—create and tag, but no edit/delete card in the teaching surface—so product policy for card lifecycle is undefined.)*

---

## Open question with more than one defensible answer

**Should “study sessions” (or reviews) be a first-class entity?**

- **One defensible answer: no entity yet** — The app is a **content** catalog (decks, cards, tags). Actual study happens offline or in the user’s head; persisting sessions adds complexity and retention policy without clear value.

- **Another defensible answer: yes, add `study_session` (or events)** — If the product goal shifts to **spaced repetition**, progress, or analytics, then sessions or per-card review events become central. You might store start/end time, mode, and outcomes; that touches privacy (how fine-grained is “you studied card 42 at 9:02?”).

- **A middle path:** derive metrics from **append-only review events** without a heavy “session” header row—still a schema and privacy choice.

The current project does not force an answer; the diagram and migrations stay silent. Choosing among these is product strategy, not something readable directly from the code.

---

## What remains open to redesign

Nothing in the teaching schema is sacred for a real product. **`card_tags`** might gain relationship attributes or stricter delete rules; **`tags`** might become user-scoped, shared across a workspace, or a global curated taxonomy; **`decks` / `cards`** might split into “library” vs “instance” if content is reused; a **`users`** table might be replaced by “bring your own identity” with only opaque subject ids. Those forks are **not** prescribed here—only the distinction matters: **reconstruct what the repo does**, then **argue what a serious deployment would still need to decide**.

---

## Reading this with the diagram

Together, [er-diagram.md](er-diagram.md) and this note mean: **solid lines and tables marked `*`** are the teaching database as shipped; **† elements** (User, ownership, `linked_at`, per-owner uniqueness) are **analyst proposals** for a multi-user, production-shaped evolution—not bugs in the assignment. Anyone merging the two documents should see both **what exists** and **what still requires an explicit decision**.
