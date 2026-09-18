import logging
import os
import sys


def setup_logging():
    # создаём папку logs, если её ещё нет - работает как локально, так и в CI/Docker
    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log"),
        ],
    )