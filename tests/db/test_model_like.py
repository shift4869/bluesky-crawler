import sys
import unittest

from blueskycrawler.db.model import Like


class TestModelLike(unittest.TestCase):
    def get_params(self) -> dict:
        return {
            "post_id": "dummy_post_id",
            "user_id": "dummy_user_id",
            "url": "dummy_url",
            "text": "dummy_text",
            "created_at": "dummy_created_at",
            "registered_at": "dummy_registered_at",
        }

    def test_init(self):
        params = self.get_params()
        instance = Like(
            params["post_id"],
            params["user_id"],
            params["url"],
            params["text"],
            params["created_at"],
            params["registered_at"],
        )
        self.assertEqual(params["post_id"], instance.post_id)
        self.assertEqual(params["user_id"], instance.user_id)
        self.assertEqual(params["url"], instance.url)
        self.assertEqual(params["text"], instance.text)
        self.assertEqual(params["created_at"], instance.created_at)
        self.assertEqual(params["registered_at"], instance.registered_at)

        another_instance = Like(
            params["post_id"],
            params["user_id"],
            params["url"],
            params["text"],
            params["created_at"],
            params["registered_at"],
        )
        self.assertEqual(f"<Like(post_id='{params["post_id"]}')>", repr(instance))
        self.assertTrue(instance == another_instance)
        another_instance.post_id = "another_post_id"
        self.assertTrue(instance != another_instance)

    def test_create(self):
        params = self.get_params()
        instance = Like.create(params)
        another_instance = Like(
            params["post_id"],
            params["user_id"],
            params["url"],
            params["text"],
            params["created_at"],
            params["registered_at"],
        )
        self.assertEqual(instance, another_instance)

        with self.assertRaises(ValueError):
            instance = Like.create({"invalid_dict_key": "invalid_dict_value"})

    def test_to_dict(self):
        params = self.get_params()
        instance = Like.create(params)
        self.assertEqual(
            {
                "post_id": "dummy_post_id",
                "user_id": "dummy_user_id",
                "url": "dummy_url",
                "text": "dummy_text",
                "created_at": "dummy_created_at",
                "registered_at": "dummy_registered_at",
            },
            instance.to_dict(),
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
