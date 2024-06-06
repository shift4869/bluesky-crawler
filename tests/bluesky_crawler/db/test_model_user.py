import sys
import unittest

from bluesky_crawler.db.model import User


class TestModelUser(unittest.TestCase):
    def get_params(self) -> dict:
        return {
            "user_id": "dummy_user_id",
            "name": "dummy_name",
            "username": "dummy_username",
            "avatar_url": "dummy_avatar_url",
            "registered_at": "dummy_registered_at",
        }

    def test_init(self):
        params = self.get_params()
        instance = User(
            params["user_id"],
            params["name"],
            params["username"],
            params["avatar_url"],
            params["registered_at"],
        )
        self.assertEqual(params["user_id"], instance.user_id)
        self.assertEqual(params["name"], instance.name)
        self.assertEqual(params["username"], instance.username)
        self.assertEqual(params["avatar_url"], instance.avatar_url)
        self.assertEqual(params["registered_at"], instance.registered_at)

        another_instance = User(
            params["user_id"], params["name"], params["username"], params["avatar_url"], params["registered_at"]
        )
        self.assertEqual(f"<User(user_id='{params["user_id"]}')>", repr(instance))
        self.assertTrue(instance == another_instance)
        another_instance.user_id = "another_user_id"
        self.assertTrue(instance != another_instance)

    def test_create(self):
        params = self.get_params()
        instance = User.create(params)
        another_instance = User(
            params["user_id"], params["name"], params["username"], params["avatar_url"], params["registered_at"]
        )
        self.assertEqual(instance, another_instance)

        with self.assertRaises(ValueError):
            instance = User.create({"invalid_dict_key": "invalid_dict_value"})

    def test_to_dict(self):
        params = self.get_params()
        instance = User.create(params)
        self.assertEqual(
            {
                "user_id": "dummy_user_id",
                "name": "dummy_name",
                "username": "dummy_username",
                "avatar_url": "dummy_avatar_url",
                "registered_at": "dummy_registered_at",
            },
            instance.to_dict(),
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
