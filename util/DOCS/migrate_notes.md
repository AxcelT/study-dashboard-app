# DOCS: migrate_notes.py

## Overview
This script is a one-off data migration tool used to convert legacy `.txt` course notes into the application's new standard Markdown (`.md`) format.

The early version of the Study Dashboard appended raw reading materials and video transcripts into flat `.txt` files separated by `===` delimiters. This script parses those legacy files, applies proper Markdown typographical hierarchy (using `#`, `##`, and `###` headers), and generates new `.md` files that are highly readable and optimized for AI ingestion.

## What it does
1. Scans the root `notes/` directory for any files ending in `.txt`.
2. Splits the text into blocks based on the `===` delimiter.
3. Automatically maps legacy headers to Markdown:
   - `Module ...` or `Article: ...` becomes an H1 (`#`).
   - `Sub-Article: ...` becomes an H2 (`##`).
   - `Video Transcript:` becomes an H3 (`###`).
4. Saves a new `.md` file in the same directory alongside the original `.txt` file.

## Usage
From your terminal, navigate to the root of the project and run the script:

`python util/migrate_notes.py`

## ⚠️ Important Warnings & Best Practices
* **Run Once:** This is designed as a one-time migration script. Once your files are converted to `.md`, you do not need to run this on the same files again.
* **Make a Backup:** Always make a copy of your `notes/` directory before running batch file manipulation scripts.
* **Cleanup:** The script does *not* delete the original `.txt` files by default. Review the generated `.md` files to ensure formatting is correct. Once verified, you can manually delete the `.txt` files or uncomment the `os.remove(txt_filepath)` line at the bottom of the script and run it one last time to auto-delete the legacy files.