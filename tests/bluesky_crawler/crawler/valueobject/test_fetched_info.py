import re
import sys
import unittest
from datetime import datetime

import freezegun
from mock import MagicMock

from bluesky_crawler.crawler.valueobject.fetched_info import FetchedInfo
from bluesky_crawler.db.model import Like, Media, User
from bluesky_crawler.util import find_values, to_jst


class TestFetchedInfo(unittest.TestCase):
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

    def test_init(self):
        like = MagicMock(spec=Like)
        user = MagicMock(spec=User)
        media_list = [MagicMock(spec=Media) for _ in range(4)]

        instance = FetchedInfo(like, user, media_list)
        self.assertEqual(like, instance.like)
        self.assertEqual(user, instance.user)
        self.assertEqual(media_list, instance.media_list)

        with self.assertRaises(ValueError):
            instance = FetchedInfo(None, user, media_list)
        with self.assertRaises(ValueError):
            instance = FetchedInfo(like, None, media_list)
        with self.assertRaises(ValueError):
            instance = FetchedInfo(like, user, None)
        with self.assertRaises(ValueError):
            instance = FetchedInfo(like, user, [])
        media_list = media_list[:2]
        media_list.extend(["invalid_element"])
        with self.assertRaises(ValueError):
            instance = FetchedInfo(like, user, media_list)

    def test_get_records(self):
        like = MagicMock(spec=Like)
        user = MagicMock(spec=User)
        media_list = [MagicMock(spec=Media) for _ in range(4)]

        instance = FetchedInfo(like, user, media_list)
        expect = [(like, user, media) for media in media_list]
        actual = instance.get_records()
        self.assertEqual(expect, actual)

    def test_create(self):
        self.enterContext(freezegun.freeze_time("2024-03-23T12:34:56"))
        fetched_dict = self.make_fetched_dict()

        def make_expect_instance():
            def normalize_date_at(date_at_str: str) -> str:
                result = to_jst(datetime.fromisoformat(date_at_str)).isoformat()
                if result.endswith("+00:00"):
                    result = result[:-6]
                return result

            registered_at = datetime.now().isoformat()
            post_dict = find_values(fetched_dict, "post", True, [""])
            author_dict = find_values(post_dict, "author", True, [""])
            record_dict = find_values(post_dict, "record", True, [""])

            embed_dict, record_embed_dict = {}, {}
            media_list_1, media_list_2 = [], []
            embed_dict = find_values(post_dict, "embed", True, [""])
            record_embed_dict = find_values(record_dict, "embed", True, [""])
            media_list_1 = find_values(embed_dict, "images", True, [""])
            media_list_2 = find_values(record_embed_dict, "images", True, [""])

            uri: str = find_values(post_dict, "uri", True, [""])
            post_id = uri.split(r"/")[-1]
            post_created_at = normalize_date_at(find_values(record_dict, "created_at", True, [""]))

            user_username = find_values(author_dict, "handle", True, [""])

            media_list = []
            for media_dict_1, media_dict_2 in zip(media_list_1, media_list_2):
                media_url: str = find_values(media_dict_1, "fullsize", True, [""])
                media_alt_text = find_values(media_dict_1, "alt", True, [""])
                media_id = re.findall(r"^.*/(.+)@.*?$", media_url)[0]
                media_mime_type = find_values(media_dict_2, "mime_type", True)
                media_size = find_values(media_dict_2, "size", True)
                media_created_at = post_created_at
                media = Media.create({
                    "post_id": post_id,
                    "media_id": media_id,
                    "username": user_username,
                    "alt_text": media_alt_text,
                    "mime_type": media_mime_type,
                    "size": media_size,
                    "url": media_url,
                    "created_at": media_created_at,
                    "registered_at": registered_at,
                })
                media_list.append(media)

            user_id = find_values(author_dict, "did", True, [""])
            post_url = f"https://bsky.app/profile/{user_username}/post/{post_id}"
            post_text = find_values(record_dict, "text", True, [""])
            like = Like.create({
                "post_id": post_id,
                "user_id": user_id,
                "url": post_url,
                "text": post_text,
                "created_at": post_created_at,
                "registered_at": registered_at,
            })

            user_name = find_values(author_dict, "display_name", True, [""]) or user_username
            user_avatar_url = find_values(author_dict, "avatar", True, [""])
            user = User.create({
                "user_id": user_id,
                "name": user_name,
                "username": user_username,
                "avatar_url": user_avatar_url,
                "registered_at": registered_at,
            })

            return FetchedInfo(like, user, media_list)

        expect = make_expect_instance()
        actual = FetchedInfo.create(fetched_dict)
        self.assertEqual(expect, actual)

        fetched_dict = self.make_fetched_dict()
        del fetched_dict["post"]["embed"]
        with self.assertRaises(ValueError):
            actual = FetchedInfo.create(fetched_dict)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
