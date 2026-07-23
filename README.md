# Study Dashboard

A local-first, Coursera-style study dashboard built with Flask. Course material
is stored as plain files on disk (no database) and presented in a split view:
the raw copy-pasted transcript on the left, and an AI-compiled study guide
rendered as Markdown on the right.

> **Status (2026-07-18):** Sprint 1 complete — dashboard, structure management,
> compiler, and migration tooling are working. The AI side is a placeholder;
> Gemini API integration is the next major feature. See
> [DOCS/Sprint1.md](DOCS/Sprint1.md) for the full sprint report.

## Features

- **Dashboard** (`/`) — sidebar navigation (course dropdown → collapsible
  modules → articles → sub-articles) with a split-pane reader: raw transcript
  beside the rendered study guide, each pane scrolling independently.
- **Manage Structure** (`/manage`) — create, rename, and reorder courses,
  modules, and articles from the browser; new items are auto-numbered.
- **Notes Compiler** (`/compiler`) — paste transcripts or readings, attach
  screenshots with inline `[[MEDIA_n]]` placeholders, and have them filed into
  the hierarchy automatically.
- **Migration utilities** (`util/`) — batch converters for legacy note formats,
  documented in [util/DOCS](util/DOCS).

## How content is stored

```text
notes\<course>\<xx_module>\<xx_article>\<xx_subarticle>.md      <- raw pasted content
notes\<course>\<xx_module>\<xx_article>\<xx_subarticle>.ai.md   <- AI study guide (placeholder until generated)
```

- **Course** = a certificate (e.g. `aws_cloud_support_professional`).
- **Modules, articles, and sub-articles** carry `xx_` numeric prefixes that
  control their order in the sidebar.
- Each sub-article is a file pair sharing one stem; the `.ai.md` suffix keeps
  the pair adjacent in listings.
- `notes\` is gitignored — study content is personal data and never ships with
  the repo.

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.1.3 (single `app.py`) |
| Markdown rendering | `Markdown` 3.10.2 (server-side) |
| Frontend | HTML/CSS (flexbox), Jinja2 templates, no JS framework |
| Storage | Filesystem under `notes\` |
| Logging | Rotating file logs in `logs\` (1 MB × 3 files) |

## Setup

1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open http://localhost:5000 — use **Manage Structure** to create your first
   course/module/article, then the **Notes Compiler** to paste in content.

## Migrating old notes

Legacy single-file module notes can be converted into the hierarchy with:

```bash
python util/migrate_md_to_hierarchy.py            # preview into util/output/
python util/migrate_md_to_hierarchy.py --install  # merge into notes/
```

See [util/DOCS/migrate_md_to_hierarchy.md](util/DOCS/migrate_md_to_hierarchy.md)
for the full workflow and warnings.

## Roadmap

1. **Gemini API integration** — generate each sub-article's `.ai.md` study
   guide from its raw transcript (the core upcoming feature).
2. Serve media images from `notes\` so attachments render in the reader panes.
3. Delete operations (with confirmation) in Manage Structure.
4. Harden beyond local use (real secret key, debug off, auth) if ever deployed.

## Project documentation

- [DOCS/Sprint1.md](DOCS/Sprint1.md) — end-of-sprint snapshot: full feature
  inventory, verification notes, known gaps.
- [util/DOCS](util/DOCS) — per-utility documentation with changelogs.
