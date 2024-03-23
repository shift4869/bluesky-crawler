import sys
import unittest

from mock import patch

from blueskycrawler.db.base import Base


class ConcreteMobel(Base):
    def select(self):
        return []

    def upsert(self, record):
        return []


class TestBase(unittest.TestCase):
    def test_init(self):
        mock_create_engine = self.enterContext(patch("blueskycrawler.db.base.create_engine"))
        mock_model_base = self.enterContext(patch("blueskycrawler.db.base.ModelBase"))
        instance = ConcreteMobel()

        mock_create_engine.assert_called_once()
        mock_create_engine.assert_called_once()

        db_path = "bksy_db.db"
        self.assertEqual(db_path, instance.db_path)
        self.assertEqual(f"sqlite:///{db_path}", instance.db_url)
        self.assertEqual([], instance.select())
        self.assertEqual([], instance.upsert(None))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
