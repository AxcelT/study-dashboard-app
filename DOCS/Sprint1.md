# Sprint 1 Report: Study Dashboard

> **Written:** 2026-07-18 (end of Sprint 1)
> **Branch state:** `Sprint-1` complete, draft PR #1 open against `main`.
>
> This document is a point-in-time snapshot of the project at the end of
> Sprint 1. For the living project overview, see the root [README](../README.md).

## What this program is

A local-first, Coursera-style study dashboard built with Flask. It stores course
material as plain files on disk (no database) and presents each lesson in a
split view: the raw copy-pasted transcript on the left, and an AI-compiled
study guide rendered as Markdown on the right. The AI side is currently a
placeholder — the Gemini API integration is planned but not started.

The app began life as a notes *compiler* (a form that appended pasted
transcripts into flat files). That tool still exists inside the app; the
dashboard grew around it during Sprint 1.

## Current stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.1.3 (Python, single `app.py`) |
| Templating | Jinja2 |
| Markdown rendering | `Markdown` 3.10.2 (server-side, tables + fenced code) |
| Frontend | Plain HTML/CSS (flexbox), no JS framework |
| Storage | Filesystem under `notes\` |
| Logging | Rotating file logs in `logs\` (1 MB × 3 files) |

Run locally: `python app.py` → http://localhost:5000 (debug mode).

## Data model (filesystem hierarchy)

```text
notes\<course>\<xx_module>\<xx_article>\<xx_subarticle>.md      <- raw pasted content
notes\<course>\<xx_module>\<xx_article>\<xx_subarticle>.ai.md   <- AI study guide (placeholder text until generated)
```

- **Course** = a certificate (e.g. `aws_cloud_support_professional`). Not numbered.
- **Module / Article** = folders with `xx_` numeric prefixes that control sidebar order.
- **Sub-article** = a pair of files sharing one stem; `.ai.md` keeps the pair
  adjacent in listings. Media images live in a `media\` folder beside the pairs.
- `notes\` is **gitignored** — content is personal data and never ships with the repo.

## Implemented features (working and verified)

### Dashboard — `/` and `/view/<course>/<module>/<article>/<sub>`
- Sidebar: course dropdown → collapsible module sections → article groups →
  sub-article links. Active item highlighted; ⏳ marks sub-articles with no AI
  artifact yet.
- Split-pane reader with independently scrolling panes; raw pane is monospace
  with preserved line breaks, guide pane styles rendered Markdown.
- Slug validation + `safe_join` on all path segments (traversal attempts 404).

### Manage Structure — `/manage`
- Create courses, modules, and articles (auto-numbered at the end of their sequence).
- Rename and/or reorder any item by new name and position number.
- Live tree of the on-disk structure; flash messages confirm every action.

### Notes Compiler — `/compiler`
- Routes pasted content to course/module/article (names match existing folders
  with or without their `xx_` prefix; unknown names are created auto-numbered).
- Writes the sub-article `.md` (appends with a `---` divider on resubmission)
  and seeds the `.ai.md` placeholder — never overwrites a real artifact.
- Multi-image upload with `[[MEDIA_n]]` inline placeholders.

### Migration utilities — `util\`
Named by transformation (input → output), each documented in `util\DOCS\`:
- `migrate_txt_to_md.py` — legacy flat `.txt` notes → formatted `.md` (historic, one-off).
- `migrate_md_to_hierarchy.py` — legacy single-file `.md` modules → the folder
  hierarchy. `input/` → `output/` workflow with `--install` merge into `notes\`;
  cleans Coursera copy-paste artifacts (zero-width chars, `[CTRL + S]` junk,
  duplicated transcript paragraphs) and de-duplicates repeated sub-articles.
  Already run against the three legacy files of `01_intro_to_it_and_aws`
  (5 articles, 32 sub-article pairs).

## Current content state (local)

- `aws_cloud_support_professional` with real module folders `01`–`06`.
- Migrated content fills `01_intro_to_it_and_aws` (articles 01–05).
- Two sample/demo articles remain from development and can be deleted:
  `01_intro_to_it_and_aws\01_cloud_foundations` and
  `04_cloud_support_essentials\01_networking_basics`.
- Some junk sub-articles from old compiler tests survived migration under
  `04_internet_101` (`04_test`, `05_reading_test`, `06_test_2`) — delete at will.

## Known gaps / not yet implemented

1. **Gemini API integration** — the core upcoming feature. Every `.ai.md` is
   placeholder text; there is no generate/regenerate action yet. The natural
   hook is a per-sub-article action on the dashboard or manage page.
2. **No delete operations** in the Manage page (create/rename/reorder only).
   Deleting content means removing folders in the file explorer.
3. **Media files don't render** in the dashboard panes — image links are stored
   in the Markdown but no Flask route serves files from `notes\`.
4. **Raw pane shows plain text only** — raw `.md` files are displayed verbatim,
   not rendered.
5. **README.md is stale** — it still describes the pre-dashboard compiler app.
6. **Dev-only hardening** — hardcoded Flask `secret_key`, debug mode on,
   no auth. Fine for local single-user use; not deployable as-is.
7. **Compiler duplicate handling** is append-only; there is no edit/replace of
   an existing sub-article from the UI.

## Suggested next steps (in rough priority order)

1. Wire up the Gemini API: a "Generate study guide" action that reads a
   sub-article's raw `.md` and writes its `.ai.md`.
2. Serve media from `notes\` and render images in both panes.
3. Update README.md to describe the dashboard.
4. Add delete (with confirmation) to Manage Structure.

## Changelog

| Date | Change |
|------|--------|
| 2026-07-18 | Created at the end of Sprint 1 |
