import os

# Agent classes raise ValueError if GROQ_API_KEY is missing when they're
# constructed. Tests never make a real API call, so a dummy value is enough
# to let Orchestrator() and ResearchAgent() initialize normally.
os.environ.setdefault("GROQ_API_KEY", "test-key-for-pytest")