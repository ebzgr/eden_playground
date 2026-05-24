# Documentation conventions

Two doc trees. They are not interchangeable.

## `/docs/` — human-facing wiki

- Audience: humans (project lead, collaborators, reviewers).
- Format: HTML pages with a shared sidebar, plus a few `*.md` files like [`/docs/Architecture.md`](../../docs/Architecture.md).
- Tone: explanatory, narrative, illustrated. Mission, ethics, methodology, worlds, brainstorming.
- Linked from [`/docs/index.html`](../../docs/index.html).

When to update:

- Architecture or capability changes — [`/docs/Architecture.md`](../../docs/Architecture.md) and/or [`/docs/architecture.html`](../../docs/architecture.html).
- New feature visible to humans — touch [`/docs/index.html`](../../docs/index.html) if it changes the navigation or the top-level overview.
- New world or major scene change — touch [`/docs/worlds.html`](../../docs/worlds.html) where appropriate.
- Conceptual or methodological shifts — [`/docs/conceptual.html`](../../docs/conceptual.html), [`/docs/research-methodology.html`](../../docs/research-methodology.html), [`/docs/ethics.html`](../../docs/ethics.html).

## `ai_docs/` — AI-facing operational manual

- Audience: AI agents (Cursor, sub-agents, future automations).
- Format: Markdown only. Short, scannable, full of file paths.
- Tone: operational. "Do this, then this, then that."
- Entry point: [`ai_docs/README.md`](../README.md).

When to update:

- The behavior, public interface, file layout, or workflow of a service changes — update its `ai_docs/services/<svc>.md`.
- A coding, documentation, or testing rule changes — update `ai_docs/conventions/*.md`.
- A role's triggers, required reading, or hand-off changes — update its `ai_docs/roles/<role>.md`.

## The update rule

> When you change behavior, file layout, public interface, or conventions of a service, you MUST update its `ai_docs/services/<service>.md` in the same change. Update `ai_docs/conventions/*.md` when the rule itself changes. Stale AI helpers are treated as an incomplete task — same standard as `/docs/`.

## Pairing rule

Most meaningful code changes touch **both** trees:

| Change | `/docs/` to update | `ai_docs/` to update |
|---|---|---|
| New service, schema, or endpoint | `Architecture.md`, possibly `architecture.html`, `tech-stack.html` | matching `services/<svc>.md` |
| New world or scene | `worlds.html` (when relevant) | `services/world_builder.md` |
| New experiment kind / lifecycle action | `Architecture.md` | `services/ab_testing.md` |
| JS SDK surface change (`playground.js` / `tracker.js` / `events.js`) | `Architecture.md` if it affects how scenes integrate | `services/event_tracker.md`, `services/world_builder.md` if the page shell changed |
| Ethics or methodology shift | `ethics.html`, `research-methodology.html`, `conceptual.html` | `roles/ethics_reviewer.md`, `roles/researcher.md` |
| New role or change to an existing role | only if the role appears in `/docs/conceptual.html` Agent-First section | matching `roles/<role>.md`, plus the role index in `README.md` |

If only one tree is updated, the task is not done.

## Role file template

Every file in [`ai_docs/roles/`](../roles/) follows the same 5-section template so any agent can scan a role in seconds. When adding or rewriting a role, keep these sections in this order:

1. **Purpose** — one paragraph: what this role optimizes for.
2. **When to activate this role** — bullet list of triggers; optionally a bullet list of "do not activate for".
3. **Required reading before acting** — exact file paths the role must read first.
4. **Operating checklist** — numbered, concrete steps the role follows.
5. **Hand-off** — who to dispatch to next and what artifact to produce. Add a **Footguns** section after this when there are real, learned pitfalls worth flagging.

Role files should be 30–60 lines. If a role's file grows past 80 lines, split conceptual material into a service or convention helper and link to it from the role.

## Style

- Backticks for file paths, function names, env vars, and HTTP routes.
- Mermaid for flow and state diagrams (no inline colors, no spaces in node ids — see the project's mermaid syntax rules).
- No emoji in either tree unless the user explicitly asks.
- Cite file paths as relative markdown links from the doc to the file (e.g. `[playground/db.py](../../playground/db.py)` from `ai_docs/conventions/*`).
- Prefer "open this file" over inlining code samples. Code drift faster than docs; paths do not.
