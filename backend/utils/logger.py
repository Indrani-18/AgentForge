import logging
from pathlib import Path


LOG_FOLDER = Path("logs")
LOG_FOLDER.mkdir(exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_FOLDER / "agentforge.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)


logger = logging.getLogger("agentforge")