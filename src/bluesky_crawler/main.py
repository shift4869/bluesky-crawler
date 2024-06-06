import logging.config
from logging import INFO, getLogger

from bluesky_crawler.crawler.crawler import Crawler

logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
# for name in logging.root.manager.loggerDict:
#     if "bluesky_crawler" not in name:
#         getLogger(name).disabled = True
logger = getLogger(__name__)
logger.setLevel(INFO)


def main() -> None:
    horizontal_line = "-" * 80
    logger.info(horizontal_line)
    logger.info("Bluesky crawler -> start")
    crawler = Crawler()
    crawler.run()
    logger.info("Bluesky crawler -> done")
    logger.info(horizontal_line)


if __name__ == "__main__":
    main()
