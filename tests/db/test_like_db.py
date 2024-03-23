import sys
import unittest

from blueskycrawler.db.like_db import LikeDB
from blueskycrawler.db.model import Like


class TestLikeDB(unittest.TestCase):
    def setUp(self) -> None:
        self.instance = self.get_instance()
        self.instance.upsert([self.make_params()])
        return super().setUp()

    def make_params(self, index: int = 0) -> dict:
        return {
            "post_id": f"post_id_{index}",
            "user_id": f"user_id_{index}",
            "url": "dummy_url",
            "text": "dummy_text",
            "created_at": "dummy_created_at",
            "registered_at": "dummy_registered_at",
        }

    def get_instance(self) -> LikeDB:
        instance = LikeDB(db_path=":memory:")
        return instance

    def test_init(self):
        self.assertEqual(":memory:", self.instance.db_path)
        self.assertEqual("sqlite:///:memory:", self.instance.db_url)

    def test_select(self):
        actual = self.instance.select()
        expect = [Like.create(self.make_params())]
        self.assertEqual(expect, actual)

    def test_upsert(self):
        def get_record(index: int) -> Like:
            return Like.create(self.make_params(index))

        def get_updated_record(index: int) -> Like:
            record = get_record(index)
            args_dict = record.to_dict() | {"registered_at": f"updated_registered_at_{index}"}
            return Like.create(args_dict)

        def strict_check(e_list: list[Like], a_list: list[Like]) -> bool:
            def strict_check_element(e: Like, a: Like) -> bool:
                return (e.to_dict() | {"id": None}) == (a.to_dict() | {"id": None})

            return all([strict_check_element(e, a) for e, a in zip(e_list, a_list)])

        # insert, 単一
        record = get_record(1)
        actual = self.instance.upsert(record)
        self.assertEqual([0], actual)
        actual = self.instance.select()
        expect = [get_record(0), get_record(1)]
        self.assertTrue(strict_check(expect, actual))

        # update, 単一
        record = get_updated_record(1)
        actual = self.instance.upsert(record)
        self.assertEqual([1], actual)
        actual = self.instance.select()
        expect = [get_record(0), get_updated_record(1)]
        self.assertTrue(strict_check(expect, actual))

        # insert, 複数
        record = [get_record(2), get_record(3)]
        actual = self.instance.upsert(record)
        self.assertEqual([0, 0], actual)
        actual = self.instance.select()
        expect = [get_record(0), get_updated_record(1), get_record(2), get_record(3)]
        self.assertTrue(strict_check(expect, actual))

        # update, 複数
        record = [get_updated_record(2), get_updated_record(3)]
        actual = self.instance.upsert(record)
        self.assertEqual([1, 1], actual)
        actual = self.instance.select()
        expect = [get_record(0), get_updated_record(1), get_updated_record(2), get_updated_record(3)]
        self.assertTrue(strict_check(expect, actual))

        # insert/update ミックス, 複数
        record = [get_updated_record(0), get_record(4)]
        actual = self.instance.upsert(record)
        self.assertEqual([1, 0], actual)
        actual = self.instance.select()
        expect = [
            get_updated_record(0),
            get_updated_record(1),
            get_updated_record(2),
            get_updated_record(3),
            get_record(4),
        ]
        self.assertTrue(strict_check(expect, actual))

        # 不正なrecord
        with self.assertRaises(TypeError):
            actual = self.instance.upsert("invalid_record")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
