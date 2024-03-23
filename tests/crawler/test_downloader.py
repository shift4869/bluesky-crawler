import shutil
import sys
import unittest
from logging import getLogger
from pathlib import Path

from mock import MagicMock, call, patch

from blueskycrawler.crawler.downloader import Downloader
from blueskycrawler.db.model import Media


class TestDownloader(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # asynio のログ抑制
        asyncio_logger = getLogger("asyncio")
        self.asyncio_log_flag = asyncio_logger.disabled
        asyncio_logger.disabled = True

        # テスト用保存先パス
        self.save_base_path = Path("./tests/config/test_base_path/")
        return super().setUp()

    def tearDown(self) -> None:
        # asynio のログ設定をもとに戻す
        getLogger("asyncio").disabled = self.asyncio_log_flag

        # テスト用保存先を削除
        shutil.rmtree(self.save_base_path, ignore_errors=True)
        return super().tearDown()

    def get_instance(self) -> Downloader:
        mock_logger = self.enterContext(patch("blueskycrawler.crawler.downloader.logger"))
        config_path = Path("./tests/config/config.json")
        instance = Downloader(config_path)
        return instance

    def test_init(self):
        instance = self.get_instance()
        self.assertEqual(self.save_base_path, instance.save_base_path)
        self.assertEqual(300, instance.save_num)
        self.assertTrue(instance.save_base_path.exists())

    async def test_worker(self):
        mock_client = self.enterContext(patch("blueskycrawler.crawler.downloader.httpx.AsyncClient"))
        media = Media.create({
            "post_id": "dummy_post_id",
            "media_id": "dummy_media_id",
            "username": "dummy_username",
            "alt_text": "dummy_alt_text",
            "mime_type": "image/jpeg",
            "size": "dummy_size",
            "url": "dummy_url",
            "created_at": "dummy_created_at",
            "registered_at": "dummy_registered_at",
        })
        filename = media.get_filename()

        async def client_get(url):
            r = MagicMock()
            r.content = str(url).encode()
            return r

        mock_client.return_value.__aenter__.return_value.get.side_effect = client_get
        instance = self.get_instance()
        actual = await instance.worker(media)
        self.assertIsNone(actual)
        self.assertTrue((self.save_base_path / filename).exists())

        actual = await instance.worker(media)
        self.assertIsNone(actual)
        self.assertTrue((self.save_base_path / filename).exists())

    async def test_excute(self):
        mock_client = self.enterContext(patch("blueskycrawler.crawler.downloader.httpx.AsyncClient"))
        media_list = [
            Media.create({
                "post_id": f"dummy_post_id_{i}",
                "media_id": f"dummy_media_id_{i}",
                "username": f"dummy_username_{i}",
                "alt_text": f"dummy_alt_text_{i}",
                "mime_type": "image/jpeg",
                "size": "dummy_size",
                "url": "dummy_url",
                "created_at": "dummy_created_at",
                "registered_at": "dummy_registered_at",
            })
            for i in range(5)
        ]

        async def client_get(url):
            r = MagicMock()
            r.content = str(url).encode()
            return r

        mock_client.return_value.__aenter__.return_value.get.side_effect = client_get
        instance = self.get_instance()
        actual = await instance.excute(media_list)
        self.assertIsNone(actual)
        for media in media_list:
            filename = media.get_filename()
            self.assertTrue((self.save_base_path / filename).exists())

    def test_download(self):
        mock_logger = self.enterContext(patch("blueskycrawler.crawler.downloader.logger"))
        mock_excute = self.enterContext(patch("blueskycrawler.crawler.downloader.Downloader.excute"))
        instance = self.get_instance()
        actual = instance.download("dummy_media_list")
        self.assertIsNone(actual)
        self.assertEqual([call("dummy_media_list")], mock_excute.mock_calls)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
