import logging
import sys


def setup_logging():
    # настраиваем формат: время - уровень важности - откуда - само сообщение
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            # вывод в консоль (попадёт в docker compose logs)
            logging.StreamHandler(sys.stdout),
            # вывод в файл - сохраняется на диске, не теряется при перезапуске контейнера,
            # если папка logs подключена как volume
            logging.FileHandler("logs/app.log"),
        ],
    )
