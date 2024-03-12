import time
from logging import getLogger
from pathlib import Path

from blueskycrawler.crawler.downloader import Downloader
from blueskycrawler.crawler.fetcher import Fetcher
from blueskycrawler.crawler.valueobject.fetched_info import FetchedInfo
from blueskycrawler.db.like_db import LikeDB
from blueskycrawler.db.media_db import MediaDB
from blueskycrawler.db.user_db import UserDB

logger = getLogger(__name__)


class Crawler:
    fetcher: Fetcher
    like_db: LikeDB
    user_db: UserDB
    media_db: MediaDB
    config_path: Path = Path("./config/config.json")

    def __init__(self) -> None:
        logger.info("Crawler init -> start")
        self.fetcher = Fetcher(self.config_path)
        self.downloader = Downloader(self.config_path)
        self.like_db = LikeDB()
        self.user_db = UserDB()
        self.media_db = MediaDB()
        logger.info("Crawler init -> done")

    def run(self) -> None:
        logger.info("Crawler run -> start")

        # fetch
        start_time = time.time()
        fetched_list: list[FetchedInfo] = self.fetcher.fetch()
        elapsed_time = time.time() - start_time
        logger.info(f"Fetching : {elapsed_time} [sec].")
        # if len(fetched_list) == 0:
        #     logger.info("No reaction created from last reaction.")
        #     logger.info("Crawler run -> done")
        #     return

        # FetchedInfo をそれぞれのリストに分解
        like_list, user_list, media_list = [], [], []
        for fetched_record in fetched_list:
            records = fetched_record.get_records()
            for record in records:
                note, user, media = record
                if note not in like_list:
                    like_list.append(note)
                if user not in user_list:
                    user_list.append(user)
                if media not in media_list:
                    media_list.append(media)

        # メディアダウンロード・保存
        logger.info(f"Num of new media is {len(media_list)}.")
        start_time = time.time()
        self.downloader.download(media_list)
        elapsed_time = time.time() - start_time
        logger.info(f"Download : {elapsed_time} [sec].")

        # DB操作
        logger.info("DB control -> start.")
        self.like_db.upsert(like_list)
        self.user_db.upsert(user_list)
        self.media_db.upsert(media_list)
        logger.info("DB control -> done.")
        logger.info("Crawler run -> done")


if __name__ == "__main__":
    import logging.config
    from logging import getLogger

    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    logger = getLogger(__name__)
    crawler = Crawler()
    crawler.run()
