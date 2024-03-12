import logging.config
from logging import getLogger

from blueskycrawler.crawler.crawler import Crawler

logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
logger = getLogger(__name__)


def main():
    horizontal_line = "-" * 80
    logger.info(horizontal_line)
    logger.info("Bluesky crawler -> start")
    crawler = Crawler()
    crawler.run()
    logger.info("Bluesky crawler -> done")
    logger.info(horizontal_line)


if __name__ == "__main__":
    main()
