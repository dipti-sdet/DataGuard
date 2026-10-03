# Environment

Versions this project was set up and run with. Keep this file up to date when you upgrade anything.

## Setup machine (Windows, Oct 2026)
| Tool | Version | Installer file |
|---|---|---|
| Python | 3.14.8 (64-bit) | `python-3.14.8-amd64.exe` |
| Git | 2.56.0 (64-bit) | `Git-2.56.0-64-bit.exe` |
| VS Code | 1.140.0 (user install, x64) | `VSCodeUserSetup-x64-1.140.0.exe` |
| pytest | latest from `requirements.txt` | `pip install -r requirements.txt` |

## Requirements
- Python 3.9 or newer. The code uses only the standard library (`sqlite3`, `argparse`, `dataclasses`); pytest is only needed for the tests.
- SQLite 3.25 or newer, because the ETL uses window functions (`ROW_NUMBER() OVER`). It is bundled with Python, so there is nothing to install.
- Git with the default branch set to `main`.

## Check your versions
    python --version
    git --version
    python -c "import sqlite3; print(sqlite3.sqlite_version)"
    pytest --version

## Authoring notes
The framework logic was first run and checked with Python 3.12 and SQLite 3.45. If something behaves differently on a newer Python, note it in the table below.

## Change log
| Date | Change |
|---|---|
| Oct 2026 | Initial setup: Python 3.14.8, Git 2.56.0, VS Code 1.140.0 |
