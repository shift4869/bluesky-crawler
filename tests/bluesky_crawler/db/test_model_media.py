import sys
import unittest

from bluesky_crawler.db.model import Media


class TestModelMedia(unittest.TestCase):
    def get_params(self) -> dict:
        return {
            "post_id": "dummy_post_id",
            "media_id": "dummy_media_id",
            "media_index": 0,
            "username": "dummy_username",
            "alt_text": "dummy_alt_text",
            "mime_type": "dummy_mime_type",
            "size": 0,
            "url": "dummy_url",
            "created_at": "dummy_created_at",
            "registered_at": "dummy_registered_at",
        }

    def test_init(self):
        params = self.get_params()
        instance = Media(
            params["post_id"],
            params["media_id"],
            params["media_index"],
            params["username"],
            params["alt_text"],
            params["mime_type"],
            params["size"],
            params["url"],
            params["created_at"],
            params["registered_at"],
        )
        self.assertEqual(params["post_id"], instance.post_id)
        self.assertEqual(params["media_id"], instance.media_id)
        self.assertEqual(params["media_index"], instance.media_index)
        self.assertEqual(params["username"], instance.username)
        self.assertEqual(params["alt_text"], instance.alt_text)
        self.assertEqual(params["mime_type"], instance.mime_type)
        self.assertEqual(params["size"], instance.size)
        self.assertEqual(params["url"], instance.url)
        self.assertEqual(params["created_at"], instance.created_at)
        self.assertEqual(params["registered_at"], instance.registered_at)

        another_instance = Media(
            params["post_id"],
            params["media_id"],
            params["media_index"],
            params["username"],
            params["alt_text"],
            params["mime_type"],
            params["size"],
            params["url"],
            params["created_at"],
            params["registered_at"],
        )
        self.assertEqual(f"<Media(media_id='{params["media_id"]}', post_id='{params["post_id"]}')>", repr(instance))
        self.assertTrue(instance == another_instance)
        another_instance.media_id = "another_media_id"
        self.assertTrue(instance != another_instance)

    def test_create(self):
        params = self.get_params()
        instance = Media.create(params)
        another_instance = Media(
            params["post_id"],
            params["media_id"],
            params["media_index"],
            params["username"],
            params["alt_text"],
            params["mime_type"],
            params["size"],
            params["url"],
            params["created_at"],
            params["registered_at"],
        )
        self.assertEqual(instance, another_instance)

        with self.assertRaises(ValueError):
            instance = Media.create({"invalid_dict_key": "invalid_dict_value"})

    def test_to_dict(self):
        params = self.get_params()
        instance = Media.create(params)
        self.assertEqual(
            {
                "post_id": "dummy_post_id",
                "media_id": "dummy_media_id",
                "media_index": 0,
                "username": "dummy_username",
                "alt_text": "dummy_alt_text",
                "mime_type": "dummy_mime_type",
                "size": 0,
                "url": "dummy_url",
                "created_at": "dummy_created_at",
                "registered_at": "dummy_registered_at",
            },
            instance.to_dict(),
        )

    def test_get_filename(self):
        params = self.get_params()
        params |= {"url": f"https://bsky.app/profile/{params["username"]}/post/{params["post_id"]}@jpeg"}
        instance = Media.create(params)
        expect = f"{params["post_id"]}_{params["username"]}_{params["media_index"]:02}.jpeg"
        self.assertEqual(expect, instance.get_filename())

        params |= {"url": f"https://bsky.app/profile/{params["username"]}/post/{params["post_id"]}"}
        params |= {"mime_type": "image/jpeg"}
        instance = Media.create(params)
        expect = f"{params["post_id"]}_{params["username"]}_{params["media_index"]:02}.jpeg"
        self.assertEqual(expect, instance.get_filename())

        params |= {"url": f"https://bsky.app/profile/{params["username"]}/post/{params["post_id"]}"}
        params |= {"mime_type": "image/x-jpeg"}
        instance = Media.create(params)
        expect = f"{params["post_id"]}_{params["username"]}_{params["media_index"]:02}.jpeg"
        self.assertEqual(expect, instance.get_filename())

        params |= {"url": "dummy_url"}
        params |= {"mime_type": "dummy_mime_type"}
        instance = Media.create(params)
        with self.assertRaises(ValueError):
            actual = instance.get_filename()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
