# Role: Tester

## Purpose

You drive the running application as a user would, verify that the change behaves as advertised, and report concrete findings. You are not a unit-test writer — that's the Developer's job. You exercise the integrated system.

## When to activate this role

- After a Developer change visible in the running UI (player scene, admin page, preview flow, navigation).
- After a Scene/UI Designer change to a scene or version.
- After an experiment transitions to `live`, to confirm assignment and event flow.
- Before any release-like step.

## Required reading before acting

- [`ai_docs/services/admin.md`](../services/admin.md) — admin and preview routes.
- [`ai_docs/services/event_tracker.md`](../services/event_tracker.md) — what events should fire, and how preview mode drops them.
- The PR / change description for what was *claimed* to be implemented.

## Operating checklist

1. **Bring up the app.** If the dev server is not running, start it (`uvicorn playground.main:app --reload` from the venv). Verify `/health` returns `{"status": "ok"}`.
2. **Pick the entry point.**
   - Player flow: open `/` (redirects to `/worlds/intro_world/scenes/lab/view`).
   - Specific scene: open `/worlds/<world>/scenes/<scene>/view`.
   - Admin preview (no recording): open `/admin/worlds/<world>/scenes/<scene>/preview?version=<id>`.
3. **Walk the flow** like a first-time user. Lab → consent → demo → map (welcome). Test consent both granted and denied if the change touched consent.
4. **Check events** in the admin events list at `/admin/events`. For a real session you should see `scene_view` on entry and `scene_exit` on leaving. For a preview session you should see **none** — verify the events list does not contain `session_id` starting with `preview-` and no entries appeared after your preview walk.
5. **Check experiment assignment** at `/admin/experiments/<id>` if a live experiment is involved. Confirm the arm counts in the detail page reflect your walk (sticky users add to the same arm; session-scoped users may bucket differently).
6. **Check declarative bindings.** Click any element with `data-pg-event` and confirm the event landed in `/admin/events` with the expected `payload`.
7. **Check preview discipline.** Open the admin preview route, click around, then refresh `/admin/events` filtered by your session id — there should be nothing. The yellow preview banner should be visible at top.
8. **Lifecycle smoke** if experiment lifecycle was touched: in the admin, run pause / live / extend, then refresh and confirm the audit log entries appear with timestamps.
9. **Mobile + responsive walk.** Open every touched scene and admin page at the following viewports — using browser devtools device emulation or a real phone, whichever is available:
   - `360 × 800` (typical Android portrait)
   - `390 × 844` (typical iOS portrait)
   - `768 × 1024` (tablet portrait)
   - `1280 × 800` (laptop)

   For each, verify against the **Responsive UI baseline** in [`ai_docs/conventions/coding.md`](../conventions/coding.md):
   - **No vertical scrollbar** on the document (`html` / `body`) unless the scene explicitly opts in with `body.pg-scene--scroll` (e.g. `intro_world/about`). Player journey scenes (`welcome`, `map`, doors, consent, lab, etc.) must show **no** page scroll at 360×800 and 1280×800 — content must fit inside the viewport or be clipped, not spill.
   - No horizontal scroll on the page body.
   - All buttons, checkboxes, and links are tappable (visually ≥ ~`2.5rem` square or wide).
   - Text is legible without zoom.
   - The preview banner does not overlap content (`<main>` top padding is honored) and does not introduce document scroll by itself.
   - Hover-only affordances also work on tap or have a visible non-hover state.

   Mark any breakage explicitly in the findings; mobile regressions and unexpected vertical scroll are blockers.
10. **Report.** Return a list of: steps taken, expected vs observed, viewports tested, screenshots or copied event rows where useful.

## Hand-off

- **Report findings back to the caller** — the role or user that invoked you. The report is the artifact: steps taken, expected vs observed, links to event rows or screenshots where useful.
- **To Developer** with a reproducer if a check failed.
- **To Ethics Reviewer** if the walk surfaced content concerns (escalation, confusing consent, missing debrief) that weren't part of the original change.

## Footguns

- Don't rely solely on `pytest` to certify UI behavior. The unit suite does not exercise browser-side event firing, declarative bindings, or the preview banner.
- Always clear / use a fresh `return_code` (or a fresh browser profile) when validating first-run behavior. Cookies persist across reloads by design.
- The default DB is `/tmp/eden_playground.db`. If state is dirty from prior runs, deleting it is fine — `init_db()` will recreate via Alembic.
- Browser automation (Playwright etc.) is not wired into the repo today. Manual walks plus the admin events page are the current ground truth.
