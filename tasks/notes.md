# Notes

Running log of decisions, conventions, known fixes, and things to remember. Claude reads this at the start of every session.

---

## Code Conventions

> Define your project's coding style here. Agents read this section to follow your patterns.
> Below is an example — replace with your own conventions.

**Language:** Python 3.10+

**Build command:** `pip install -e .`
**Test command:** `python -m pytest tests/ -v`
**Lint command:** `ruff check transclipt/ tests/`

**Naming:**
- snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants
- Test files: `tests/test_*.py`

**Patterns:**
- Frozen dataclasses for all data transfer objects
- Type annotations on all function signatures
- Immutable data — never mutate, always return new objects

---

## PRD Configuration

Where PRDs are stored. The `/prd` skill reads this at start to determine output mode.

```
prd_mode = YOUR_PRD_MODE
```

Options:
- `file` — write `PRD.md` to the repo (default)
- `tracker` — publish as a tracker issue only
- `both-file-canonical` — file + tracker; file is canonical
- `both-tracker-canonical` — file + tracker; tracker is canonical

---

## Git Rules

- **Branch naming:** `implement/<issue-id>-<short-description>` (e.g. `implement/42-dark-mode`)
- **Commit format:** `#<issue-id> <description>` (e.g. `#42 Add dark mode toggle to settings`)
- **Never** commit directly to main — always use a branch + PR

---

## Test Commands

> Skills and agents read this section to run the correct test commands for your stack.
> Fill in every command that applies to your project. Leave others as `<!-- not applicable -->`.

**Level 1 — Build + Unit Tests (no external dependencies):**
- Build: `pip install -e .`
- Unit tests: `python -m pytest tests/ -v`

**Level 2 — Integration Tests (may require Docker/emulators):**
- Setup: not applicable (external services)
- Integration tests: not applicable
- Cleanup: not applicable

**Level 3 — Dev Server (for manual testing):**
- Dev server: not applicable (CLI tool)
- Dev server URL: not applicable

**Test filtering (for verify commands):**
- Run a specific test file: `python -m pytest tests/test_formatter.py -v`
- Run a specific test: `python -m pytest tests/test_formatter.py::test_name -v`

---

## Known Fixes

<!-- Add entries when you discover something non-obvious that fixes a recurring problem. -->
<!-- | Date | Problem | Fix | -->
<!-- | 2026-04-10 | Docker build fails on M1 | Add `--platform linux/amd64` to docker build | -->

---

## Decisions

<!-- Record why you chose approach A over approach B — future-you will thank present-you. -->
<!-- | Date | Decision | Why | -->
<!-- | 2026-04-08 | Use SQLite instead of Postgres for dev | Simpler local setup, no Docker needed | -->

---

## Blockers

<!-- Things waiting on external action — APIs, people, services. -->
<!-- | What | Waiting on | Since | -->
<!-- | API v2 access | Third-party approval | 2026-04-05 | -->
