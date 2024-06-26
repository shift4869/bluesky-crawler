import sys
import unittest

from mock import call, patch

from bluesky_crawler.main import main


class TestBlueskyCrawler(unittest.TestCase):
    def test_main(self):
        mock_logger = self.enterContext(patch("bluesky_crawler.main.logger.info"))
        mock_crawler = self.enterContext(patch("bluesky_crawler.main.Crawler"))
        actual = main()
        self.assertEqual([call(), call().run()], mock_crawler.mock_calls)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
