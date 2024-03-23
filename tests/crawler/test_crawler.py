import shutil
import sys
import unittest
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import freezegun
import orjson
from mock import MagicMock, call, patch

from blueskycrawler.crawler.crawler import Crawler
from blueskycrawler.crawler.downloader import Downloader
from blueskycrawler.crawler.fetcher import Fetcher
from blueskycrawler.crawler.valueobject.fetched_info import FetchedInfo
from blueskycrawler.db.like_db import LikeDB
from blueskycrawler.db.media_db import MediaDB
from blueskycrawler.db.model import Media
from blueskycrawler.db.user_db import UserDB
from blueskycrawler.manager.manager import BlueskyManager
from blueskycrawler.util import find_values


class TestCrawler(unittest.TestCase):
    def make_fetched_dict(self, index: int = 0, media_num: int = 4) -> dict:
        post_id = f"post_id_{index}"
        user_id = f"user_id_{index}"
        username = f"username_{index}"
        display_name = f"display_name_{index}"
        created_at = f"2024-03-23T12:34:{(index % 60):02}.897Z"
        text = f"text_{index}"
        record_embed_images = [
            {
                "alt": f"alt_{text}_{index}_{media_index}",
                "image": {
                    "mime_type": "image/jpeg",
                    "size": 100000 * (media_index + 1),
                },
            }
            for media_index in range(media_num)
        ]
        link_format = "https://cdn.bsky.app/img/feed_fullsize/plain/{}/{}@jpeg"
        embed_images = [
            {
                "alt": f"alt_{text}_{index}_{media_index}",
                "fullsize": link_format.format(f"did:plc:{user_id}", f"media_id_{index}_{media_index}"),
            }
            for media_index in range(media_num)
        ]
        return {
            "post": {
                "author": {
                    "did": f"did:plc:{user_id}",
                    "handle": f"{username}.bsky.social",
                    "avatar": "https://dummy_avatar_url@jpeg",
                    "display_name": display_name,
                },
                "cid": "dummy_cid",
                "indexed_at": "2024-03-11T05:23:56.624Z",
                "record": {
                    "created_at": created_at,
                    "text": text,
                    "embed": {"images": record_embed_images},
                },
                "uri": f"at://did:plc:{user_id}/app.bsky.feed.post/{post_id}",
                "embed": {"images": embed_images},
            },
        }

    def make_fetched_dict_list(self, fetched_dict_num: int = 5) -> dict:
        fetched_dict_list = [self.make_fetched_dict(i) for i in range(fetched_dict_num)]
        fetched_dict_list.reverse()
        return {"feed": fetched_dict_list}

    def make_fetched_list(self, fetched_dict_num: int = 5) -> list[FetchedInfo]:
        fetched_dict_list = self.make_fetched_dict_list(fetched_dict_num)
        post_list: list[dict] = find_values(fetched_dict_list, "feed", True, [""])
        post_list.reverse()
        return [FetchedInfo.create(entry) for entry in post_list]

    def test_init(self):
        mock_logger = self.enterContext(patch("blueskycrawler.crawler.crawler.logger"))
        mock_fetcher = self.enterContext(patch("blueskycrawler.crawler.crawler.Fetcher", spec=Fetcher))
        mock_downloader = self.enterContext(patch("blueskycrawler.crawler.crawler.Downloader", spec=Downloader))
        mock_like_db = self.enterContext(patch("blueskycrawler.crawler.crawler.LikeDB", spec=LikeDB))
        mock_user_db = self.enterContext(patch("blueskycrawler.crawler.crawler.UserDB", spec=UserDB))
        mock_media_db = self.enterContext(patch("blueskycrawler.crawler.crawler.MediaDB", spec=MediaDB))
        instance = Crawler()
        self.assertIsInstance(instance.fetcher, Fetcher)
        self.assertIsInstance(instance.downloader, Downloader)
        self.assertIsInstance(instance.like_db, LikeDB)
        self.assertIsInstance(instance.user_db, UserDB)
        self.assertIsInstance(instance.media_db, MediaDB)
        self.assertEqual(Path("./config/config.json"), instance.config_path)

    def test_run(self):
        self.enterContext(freezegun.freeze_time("2099-03-24T12:34:56"))
        mock_logger = self.enterContext(patch("blueskycrawler.crawler.crawler.logger"))
        mock_fetcher = self.enterContext(patch("blueskycrawler.crawler.crawler.Fetcher", spec=Fetcher))
        mock_downloader = self.enterContext(patch("blueskycrawler.crawler.crawler.Downloader", spec=Downloader))
        mock_like_db = self.enterContext(patch("blueskycrawler.crawler.crawler.LikeDB", spec=LikeDB))
        mock_user_db = self.enterContext(patch("blueskycrawler.crawler.crawler.UserDB", spec=UserDB))
        mock_media_db = self.enterContext(patch("blueskycrawler.crawler.crawler.MediaDB", spec=MediaDB))
        config_path: Path = Path("./config/config.json")
        DB_LIMIT_MEDIA_NUM = 1000
        max_fetched_list_num = (DB_LIMIT_MEDIA_NUM * 2) // 4 + 2

        def pre_run(in_db_media_flag, fetched_info_num):
            fetched_list = self.make_fetched_list(fetched_info_num)
            mock_fetcher.reset_mock()
            mock_fetcher.return_value.fetch.side_effect = lambda: fetched_list

            mock_downloader.reset_mock()
            mock_like_db.reset_mock()
            mock_user_db.reset_mock()

            mock_media_db.reset_mock()
            if in_db_media_flag:
                in_db_fetched_list = self.make_fetched_list(fetched_info_num // 2)
                in_db_media = []
                for fetched_record in in_db_fetched_list:
                    records = fetched_record.get_records()
                    for record in records:
                        _, _, media = record
                        in_db_media.append(media)
                mock_media_db.return_value.select.side_effect = lambda: in_db_media
            else:
                mock_media_db.return_value.select.side_effect = lambda: []

        def post_run(in_db_media_flag, fetched_info_num):
            fetched_list = self.make_fetched_list(fetched_info_num)
            in_db_media: list[Media] = []
            if in_db_media_flag:
                in_db_fetched_list = self.make_fetched_list(fetched_info_num // 2)
                in_db_media = []
                for fetched_record in in_db_fetched_list:
                    records = fetched_record.get_records()
                    for record in records:
                        _, _, media = record
                        in_db_media.append(media)
            else:
                in_db_media = []
            if (n := len(in_db_media)) > DB_LIMIT_MEDIA_NUM:
                in_db_media = in_db_media[n - DB_LIMIT_MEDIA_NUM :]
            in_db_media_id = [m.media_id for m in in_db_media]

            like_list, user_list, media_list = [], [], []
            for fetched_record in fetched_list:
                records = fetched_record.get_records()
                for record in records:
                    like, user, media = record
                    if media.media_id in in_db_media_id:
                        continue
                    if like not in like_list:
                        like_list.append(like)
                    if user not in user_list:
                        user_list.append(user)
                    if media not in media_list:
                        media_list.append(media)

            self.assertEqual([call(config_path), call().fetch()], mock_fetcher.mock_calls)

            if len(media_list) == 0:
                self.assertEqual([call(config_path)], mock_downloader.mock_calls)
                self.assertEqual([call()], mock_like_db.mock_calls)
                self.assertEqual([call()], mock_user_db.mock_calls)
                self.assertEqual([call(), call().select()], mock_media_db.mock_calls)
            else:
                self.assertEqual([call(config_path), call().download(media_list)], mock_downloader.mock_calls)
                self.assertEqual([call(), call().upsert(like_list)], mock_like_db.mock_calls)
                self.assertEqual([call(), call().upsert(user_list)], mock_user_db.mock_calls)
                self.assertEqual([call(), call().select(), call().upsert(media_list)], mock_media_db.mock_calls)

        Params = namedtuple("Params", ["in_db_media_flag", "fetched_info_num"])
        params_list = [
            Params(False, 5),
            Params(False, 0),
            Params(True, 5),
            Params(True, max_fetched_list_num),
        ]

        for params in params_list:
            pre_run(params.in_db_media_flag, params.fetched_info_num)
            instance = Crawler()
            actual = instance.run()
            self.assertIsNone(actual)
            post_run(params.in_db_media_flag, params.fetched_info_num)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
