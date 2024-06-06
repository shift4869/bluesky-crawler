import sys
import unittest
from datetime import datetime, timedelta

from freezegun import freeze_time
from mock import call, patch

from bluesky_crawler.util import find_values, to_jst


class TestUtil(unittest.TestCase):
    def test_find_values(self):
        sample_dict = {
            "key1": "value1",
            "key2": [
                {
                    "key3": "value3",
                }
            ],
            "multi_key": "multi_value1",
            "key4": {
                "multi_key": "multi_value2",
            },
        }
        self.assertEqual(["value1"], find_values(sample_dict, "key1"))
        self.assertEqual("value1", find_values(sample_dict, "key1", True))
        self.assertEqual(["value3"], find_values(sample_dict, "key3"))
        self.assertEqual(["value3"], find_values(sample_dict, "key3", False, ["key2"]))
        self.assertEqual(["multi_value1", "multi_value2"], find_values(sample_dict, "multi_key"))
        self.assertEqual(["multi_value1"], find_values(sample_dict, "multi_key", False, [], ["key4"]))
        self.assertEqual([], find_values(sample_dict, "invalid_key"))

        with self.assertRaises(ValueError):
            find_values(sample_dict, "invalid_key", True)
        with self.assertRaises(ValueError):
            find_values(sample_dict, "multi_key", True)

    def test_to_jst(self):
        freeze_date_str = "2024-03-15T12:34:56"
        self.enterContext(freeze_time(freeze_date_str))
        gmt = datetime.fromisoformat(freeze_date_str)
        expect = gmt + timedelta(hours=9)
        actual = to_jst(gmt)
        self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            to_jst("invalid_datetime")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
