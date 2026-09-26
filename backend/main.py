import uvicorn

from backend.api import app


if __name__ == "__main__":
    # This lets you start the server with:
    #     python backend/main.py
    # as an alternative to:
    #     uvicorn backend.main:app --reload --port 8000
    #
    # Note: --reload (auto-restart on code changes) only works
    # through the uvicorn CLI command above, not through this
    # block, so keep using that command while actively developing.
    uvicorn.run(app, host="127.0.0.1", port=8000)