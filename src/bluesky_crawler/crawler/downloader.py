import asyncio
from logging import INFO, getLogger
from pathlib import Path

import httpx
import orjson

from bluesky_crawler.db.model import Media

logger = getLogger(__name__)
logger.setLevel(INFO)


class Downloader:
    save_base_path: Path
    save_num: int

    def __init__(self, config_path: Path) -> None:
        logger.info("Downloader init -> start")
        config_dict = orjson.loads(config_path.read_bytes())
        self.save_base_path = Path(config_dict["general"]["save_base_path"])
        self.save_num = int(config_dict["general"]["save_num"])

        self.save_base_path.mkdir(parents=True, exist_ok=True)
        logger.info("Downloader init -> done")

    async def worker(self, media: Media) -> None:
        if "image" in media.mime_type:
            transport = httpx.AsyncHTTPTransport(retries=3)
            async with httpx.AsyncClient(timeout=httpx.Timeout(5, read=60), transport=transport) as client:
                url = media.url
                filename = media.get_filename()
                filepath = self.save_base_path / filename
                if filepath.exists():
                    return

                response = await client.get(url)
                response.raise_for_status()

                filepath.write_bytes(response.content)
        elif "video" in media.mime_type:
            filename = media.get_filename()
            filepath = self.save_base_path / filename
            command = [
                "ffmpeg",
                "-i",
                media.url,
                "-loglevel",
                "fatal",
                "-c",
                "copy",
                "-bsf:a",
                "aac_adtstoasc",
                filepath,
            ]
            result = await asyncio.create_subprocess_exec(*command)
            await result.wait()

    async def excute(self, media_list: list[Media]) -> None:
        task_list = [self.worker(media) for media in media_list]
        await asyncio.gather(*task_list)

    def download(self, media_list: list[Media]) -> None:
        logger.info("Downloader download -> start")
        logger.info(f"Save base path : {str(self.save_base_path)} -> start")
        asyncio.run(self.excute(media_list))
        logger.info("Downloader download -> done")


if __name__ == "__main__":
    import logging.config
    import pprint

    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    config_path = Path("./config/config.json")

    downloader = Downloader(config_path)
    media_dict1 = {
        "post_id": "3knbivgufgs2l",
        "media_id": "bafkreifeip6p4vymtovslb7gluthqlz35rkvdopfxzzggscwtm7iwuvkne",
        "media_index": 1,
        "username": "username1.bsky.social",
        "alt_text": "alt_text_1",
        "mime_type": "image/jpeg",
        "size": 641382,
        "url": "https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:3jyl327lwu4bqkfxjpihmd4a/bafkreifeip6p4vymtovslb7gluthqlz35rkvdopfxzzggscwtm7iwuvkne@jpeg",
        "created_at": "",
        "registered_at": "",
    }
    media1 = Media.create(media_dict1)
    name = media1.get_filename()
    media_dict2 = {
        "post_id": "3kks7hg4ffu22",
        "media_id": "bafkreihx2won24vnhdwwmppegwndxcueyyt6endadwer3z2jhx7owz5oqu",
        "media_index": 1,
        "username": "username2.bsky.social",
        "alt_text": "alt_text_2",
        "mime_type": "image/jpeg",
        "size": 556650,
        "url": "https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:fk56ql2ltrzfayih4y3sowur/bafkreihx2won24vnhdwwmppegwndxcueyyt6endadwer3z2jhx7owz5oqu@jpeg",
        "created_at": "",
        "registered_at": "",
    }
    media2 = Media.create(media_dict2)
    response = downloader.download([media1, media2])
    pprint.pprint(response)
