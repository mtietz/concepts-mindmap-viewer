# Contributing

Thanks for your interest in improving Concepts Mindmap Viewer.

## Getting started

1. Fork and clone the repository.
2. Create a branch from `main`.
3. Make a focused change.
4. Run the checks:

   ```bash
   python3 -m unittest discover -s tests -v
   python3 -m py_compile viewer.py desktop.py
   ```

5. Open a pull request describing what changed and why.

## Guidelines

- Keep the command-line viewer dependency-free. Discuss new desktop or build dependencies before adding them.
- Preserve local-only operation and never upload document data.
- Do not commit personal `.concept` files or other private user data.
- Add or update tests for Python behavior where practical.
- Keep changes compatible with Python 3.10 or later and current macOS releases.

## Bugs and feature requests

Open a GitHub issue with reproduction steps, the Python/macOS version, and a description of the affected Concepts file. Do not attach private documents; create a minimal non-sensitive example when one is needed.
