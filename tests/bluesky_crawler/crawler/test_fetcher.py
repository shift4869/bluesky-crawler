import sys
import unittest
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import freezegun
import orjson
from mock import patch

from bluesky_crawler.crawler.fetcher import Fetcher
from bluesky_crawler.crawler.valueobject.fetched_info import FetchedInfo


class TestFetcher(unittest.TestCase):
    def make_fetched_dict(self, index: int = 0, media_num: int = 4) -> dict:
        post_id = f"post_id_{index}"
        user_id = f"user_id_{index}"
        username = f"username_{index}"
        display_name = f"display_name_{index}"
        created_at = f"2024-03-23T12:34:{index:02}.897Z"
        text = f"text_{index}"
        record_embed_images = [
            {
                "alt": f"alt_{text}_{media_index}",
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
                "alt": f"alt_{text}_{media_index}",
                "fullsize": link_format.format(f"did:plc:{user_id}", f"media_id_{media_index}"),
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

    def test_init(self):
        mock_logger = self.enterContext(patch("bluesky_crawler.crawler.fetcher.logger"))
        mock_manager = self.enterContext(patch("bluesky_crawler.crawler.fetcher.BlueskyManager"))
        config_path = Path("./tests/bluesky_crawler/config/config.json")

        instance = Fetcher(config_path)
        config_dict = orjson.loads(config_path.read_bytes())
        mock_manager.assert_called_once_with(config_dict)
        self.assertEqual(mock_manager.return_value, instance.manager)
        self.assertEqual(False, instance.is_debug)
        self.assertEqual(Path("./cache/"), instance.cache_path)

    def test_fetch(self):
        self.enterContext(freezegun.freeze_time("2099-03-23T12:34:56"))
        mock_logger = self.enterContext(patch("bluesky_crawler.crawler.fetcher.logger"))
        mock_manager = self.enterContext(patch("bluesky_crawler.crawler.fetcher.BlueskyManager"))
        config_path = Path("./tests/bluesky_crawler/config/config.json")
        cache_path = Path("./cache/")

        def pre_run(instance, is_debug, fetched_dict_num, error_occur):
            fetched_dict_list = self.make_fetched_dict_list(fetched_dict_num)
            if error_occur:
                del fetched_dict_list["feed"][0]["post"]["embed"]
            mock_manager.return_value.get_actor_likes.side_effect = lambda limit: fetched_dict_list

            if is_debug and not error_occur:
                date_str = datetime.now().strftime("%Y%m%d%H%M%S")
                cache_filename = f"{date_str}_bluesky.json"
                save_path = cache_path / cache_filename
                save_path.write_bytes(orjson.dumps({"result": fetched_dict_list}, option=orjson.OPT_INDENT_2))

            if is_debug and error_occur:
                date_str = datetime.now().strftime("%Y%m%d%H%M%S")
                cache_filename = f"{date_str}_bluesky.json"
                save_path = cache_path / cache_filename
                save_path.unlink(missing_ok=True)
                instance.cache_path = Path("./tests/bluesky_crawler/cache/")

        def post_run(is_debug, fetched_dict_num, error_occur):
            if not is_debug and fetched_dict_num > 0:
                date_str = datetime.now().strftime("%Y%m%d%H%M%S")
                cache_filename = f"{date_str}_bluesky.json"
                save_path = cache_path / cache_filename
                self.assertTrue(save_path.exists())
                save_path.unlink(missing_ok=True)

        def make_expect(is_debug, fetched_dict_num, error_occur):
            post_list: list[dict] = self.make_fetched_dict_list(fetched_dict_num)["feed"]
            if error_occur:
                post_list = post_list[1:]
            post_list.reverse()
            return [FetchedInfo.create(entry) for entry in post_list]

        Params = namedtuple("Params", ["is_debug", "fetched_dict_num", "error_occur"])
        params_list = [
            Params(False, 5, False),
            Params(False, 5, True),
            Params(False, 0, False),
            Params(True, 5, False),
            Params(True, 5, True),
        ]

        for params in params_list:
            instance = Fetcher(config_path, params.is_debug)
            pre_run(instance, params.is_debug, params.fetched_dict_num, params.error_occur)
            actual = None
            if params.is_debug and params.error_occur:
                with self.assertRaises(ValueError):
                    actual = instance.fetch()
                continue
            else:
                actual = instance.fetch()
            expect = make_expect(params.is_debug, params.fetched_dict_num, params.error_occur)
            self.assertEqual(expect, actual)
            post_run(params.is_debug, params.fetched_dict_num, params.error_occur)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
