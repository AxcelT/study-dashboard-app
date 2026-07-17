# DOCS: migrate_md_to_hierarchy.py

## Overview
This script is a batch migration tool used to convert legacy single-file course notes into the application's new directory hierarchy.

The previous version of the Study Dashboard stored an entire Coursera course-module in one `.md` file (e.g. `01_module1.md`), with `# Module`, `# Article:`, and `## Sub-Article:` headings separating the content. The new structure stores every level as its own folder, and every sub-article as a pair of files:

```
notes\<course>\<xx_module>\<xx_article>\<xx_subarticle>.md      <- raw pasted content
notes\<course>\<xx_module>\<xx_article>\<xx_subarticle>.ai.md   <- AI artifact (placeholder)
```

This script parses the legacy files, cleans up copy-paste artifacts from Coursera, and generates that folder structure ready to drop into `notes\`.

## What it does
1. Scans the `util/input/` directory (recursively) for files ending in `.md`.
2. Maps the legacy headings onto the new hierarchy:
   - Any subfolders inside `input/` are mirrored as-is (use them for the course and module levels).
   - `# Article: ...` becomes a numbered article folder (`01_`, `02_`, ... — numbering continues across files that share the same output folder, so `01_module1.md` through `01_module3.md` produce one continuous sequence).
   - `## Sub-Article: Title (Video|Reading)` becomes a numbered file pair: `xx_title.md` with the raw content, plus `xx_title.ai.md` containing the AI artifact placeholder.
   - `# Module N: ...` week headings have no folder level in the new schema; they are listed in the run report, and used as a fallback article name if sub-articles appear before any `# Article:` heading.
3. Cleans the content on the way through:
   - Strips invisible zero-width characters and the `Added to Selection. Press [CTRL + S]...` junk that Coursera embeds in copied transcripts.
   - Removes `### Video Transcript` header lines and malformed `==` separators.
   - Collapses duplicated transcript paragraphs (accidental double/triple pastes).
   - Skips sub-articles that are exact duplicates (same title **and** same content). Same title with different content is kept with a `_2` suffix.
4. Writes the result to `util/output/` and prints a report (articles created, sub-articles saved, duplicates skipped, module headings encountered).
5. With `--install`, additionally merges `util/output/` into the project's `notes/` directory.

## Usage
1. Drop your legacy `.md` files into `util/input/`, mirroring the target course/module folders:

   ```
   util/input/aws_cloud_support_professional/01_intro_to_it_and_aws/01_module1.md
   ```

2. From the root of the project, run:

   `python util/migrate_md_to_hierarchy.py`

3. Review the generated structure in `util/output/`. When it looks right, install it into `notes/`:

   `python util/migrate_md_to_hierarchy.py --install`

## ⚠️ Important Warnings & Best Practices
* **Output is wiped each run:** `util/output/` is deleted and regenerated on every run. Never store hand-edited files there — edit in `notes/` after installing.
* **Install overwrites matching files:** `--install` merges into `notes/` and overwrites files with the same name. Re-running the same migration is safe (idempotent), but if you have manually edited a migrated file in `notes/`, re-installing will clobber those edits.
* **Make a Backup:** Copy your `notes/` directory before running `--install` for the first time on a new batch.
* **Review the report:** Check the "duplicates skipped" list after each run — the legacy files contain stray `test` entries and repeated readings, and the report tells you exactly what was dropped or suffixed.
* **Originals are untouched:** The script only reads from `util/input/`. Your legacy files are never modified or deleted; clean up `util/input/` manually once you've verified the migration.

## Changelog
| Date | Change |
|------|--------|
| 2026-07-18 | Created on this date (as `migrate.py`, renamed to `migrate_md_to_hierarchy.py` same day). |
