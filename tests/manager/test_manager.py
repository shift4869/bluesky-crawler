import sys
import unittest
from collections import namedtuple
from pathlib import Path

from mock import call, patch

from blueskycrawler.manager.manager import BlueskyManager


class TestBlueskyManager(unittest.TestCase):
    def test_init(self):
        mock_client = self.enterContext(patch("blueskycrawler.manager.manager.Client"))
        mock_client.return_value.export_session_string.side_effect = lambda: "session_string"
        config_dict = {"bluesky": {"handle_name": "__dummy_name", "password": "dummy_password"}}
        session_file = Path(f"./config/__dummy_name_session.txt")

        def pre_run(first_init, reflesh_flag):
            session_file.unlink(missing_ok=True)
            if first_init:
                return
            session_file.touch()
            if reflesh_flag:
                session_file.write_text("old_session_string", encoding="utf8")
            else:
                session_file.write_text("session_string", encoding="utf8")

        def post_run(first_init, reflesh_flag, instance: BlueskyManager):
            handle = "__dummy_name.bsky.social"
            session_string = None
            if not first_init:
                if reflesh_flag:
                    session_string = "old_session_string"
                else:
                    session_string = "session_string"

            self.assertEqual("__dummy_name", instance.handle_name)
            self.assertEqual("dummy_password", instance.password)
            self.assertEqual(handle, instance.handle)
            self.assertEqual(
                [
                    call(base_url="https://bsky.social"),
                    call().login(handle, "dummy_password", session_string),
                    call().export_session_string(),
                ],
                mock_client.mock_calls,
            )
            self.assertTrue(session_file.exists())
            session_file.unlink(missing_ok=True)
            mock_client.reset_mock()

        Params = namedtuple("Params", ["first_init", "reflesh_flag"])
        params_list = (
            Params(True, False),  # 初回
            Params(False, False),  # session_string使用（リフレッシュなし）
            Params(False, True),  # session_string使用（リフレッシュあり）
        )

        try:
            for params in params_list:
                pre_run(params.first_init, params.reflesh_flag)
                instance = BlueskyManager(config_dict)
                post_run(params.first_init, params.reflesh_flag, instance)
        finally:
            session_file.unlink(missing_ok=True)

    def test_get_actor_likes(self):
        mock_client = self.enterContext(patch("blueskycrawler.manager.manager.Client"))
        mock_client.return_value.export_session_string.side_effect = lambda: None
        mock_client.return_value.app.bsky.feed.get_actor_likes.return_value.model_dump.side_effect = (
            lambda: "get_actor_likes_model_dump"
        )
        config_dict = {"bluesky": {"handle_name": "__dummy_name", "password": "dummy_password"}}
        instance = BlueskyManager(config_dict)
        mock_client.reset_mock()
        actual = instance.get_actor_likes()
        expect = "get_actor_likes_model_dump"
        self.assertEqual(expect, actual)
        self.assertEqual(
            [
                call().app.bsky.feed.get_actor_likes(params={"actor": instance.handle, "limit": 100}),
                call().app.bsky.feed.get_actor_likes().model_dump(),
            ],
            mock_client.mock_calls,
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
