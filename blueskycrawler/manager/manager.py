import logging.config
import pprint
from logging import INFO, getLogger
from pathlib import Path

import orjson
from atproto import Client

logger = getLogger(__name__)
logger.setLevel(INFO)


class BlueskyManager:
    handle: str
    password: str
    client: Client

    def __init__(self, config_dict: dict) -> None:
        self.client = Client(base_url="https://bsky.social")
        self.handle = f"{config_dict["bluesky"]["handle_name"]}.bsky.social"
        self.password = config_dict["bluesky"]["password"]
        response = self.client.login(self.handle, self.password)

    def get_actor_likes(self, limit: int = 100) -> dict:
        params = {"actor": self.handle, "limit": limit}
        response = self.client.app.bsky.feed.get_actor_likes(params=params)
        response = response.model_dump()
        return response


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    config_path: Path = Path("./config/config.json")
    config_dict = orjson.loads(config_path.read_bytes())
    manager = BlueskyManager(config_dict)
    response = manager.get_actor_likes()
    pprint.pprint(response)
