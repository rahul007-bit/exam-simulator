"""Web backend entrypoint (facade).

The implementation lives in the web.api package (one module per task); this
module only assembles the app and keeps the historical import path working:

- core/cli.py runs: uvicorn.run("web.server:app", ...)
- host deploy verification: .venv/bin/python -c 'import web.server'
"""
from web.api import create_app

app = create_app()
