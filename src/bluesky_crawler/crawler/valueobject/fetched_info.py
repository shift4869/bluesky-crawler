import pprint
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

import orjson

from bluesky_crawler.db.model import Like, Media, User
from bluesky_crawler.util import find_values, to_jst


@dataclass(frozen=True)
class FetchedInfo:
    like: Like
    user: User
    media_list: list[Media]

    def __post_init__(self) -> None:
        """引数チェック

        media_list は空リストは許容しない

        Raises:
            ValueError: like が Like インスタンスでない
            ValueError: user が User インスタンスでない
            ValueError: media_list がリストでない
            ValueError: media_list が空リスト
            ValueError: media_list 内に Media インスタンス以外の要素が含まれる
        """
        if not isinstance(self.like, Like):
            raise ValueError("Argument like is not Like type.")
        if not isinstance(self.user, User):
            raise ValueError("Argument user is not User type.")
        if not isinstance(self.media_list, list):
            raise ValueError("Argument media_list is not list.")
        if len(self.media_list) == 0:
            raise ValueError("Argument media_list is empty.")
        if not all([isinstance(media, Media) for media in self.media_list]):
            raise ValueError("Argument media_list is include not Media type element.")

    def get_records(self) -> list[tuple[Like, User, Media]]:
        """レコードをタプルのリストにして返す

        media_list はそれぞれの media ごとに要素となるが、
        like と user は共通に付与される

        Returns:
            list[tuple[Like, User, Media]]: インスタンスのレコード
        """
        return [(self.like, self.user, media) for media in self.media_list]

    @classmethod
    def create(cls, fetched_dict: dict) -> Self:
        """fetched_info インスタンスを作成する

        fetch データの辞書解析を行う
        fetch データの辞書構造が変わった・取得情報の参照元が変わった場合はこのメソッドを更新する

        Args:
            fetched_dict (dict): fetch したデータ辞書の1レコード

        Returns:
            Self: fetched_info インスタンス
        """

        def normalize_date_at(date_at_str: str) -> str:
            """日時文字列を日本時間に変換する

            Args:
                date_at_str (str): ISOフォーマットの日時文字列(UTC)

            Returns:
                str: ISOフォーマットの日時文字列(JST)
            """
            result = to_jst(datetime.fromisoformat(date_at_str)).isoformat()
            if result.endswith("+00:00"):
                result = result[:-6]
            return result

        # 採用する登録日時を取得
        registered_at = datetime.now().isoformat()
        # fetch データの辞書解析
        post_dict = find_values(fetched_dict, "post", True, [""])
        author_dict = find_values(post_dict, "author", True, [""])
        record_dict = find_values(post_dict, "record", True, [""])

        # メディアが含まれる部分を抽出する
        embed_dict, record_embed_dict = {}, {}
        media_list_1, media_list_2 = [], []
        try:
            # post 直下の embed (直リンクとaltテキストが含まれる)と
            # record 配下の embed (mime_type と size が含まれる)がそれぞれ存在するか確認する
            embed_dict = find_values(post_dict, "embed", True, [""])
            record_embed_dict = find_values(record_dict, "embed", True, [""])
            media_list_1 = find_values(embed_dict, "images", True, [""])
            media_list_2 = find_values(record_embed_dict, "images", True, [""])
        except ValueError:
            # メディアが含まれていなかった → エラー
            raise ValueError("Like entry has no media.")

        # post 情報から post_id と created_at を抽出する
        uri: str = find_values(post_dict, "uri", True, [""])
        post_id = uri.split(r"/")[-1]
        post_created_at = normalize_date_at(find_values(record_dict, "created_at", True, [""]))

        # author 情報から username を抽出する
        user_username = find_values(author_dict, "handle", True, [""])

        # media_list 作成
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

        # like 作成
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

        # user 作成
        user_name = find_values(author_dict, "display_name", True, [""]) or user_username
        user_avatar_url = find_values(author_dict, "avatar", True, [""])
        user = User.create({
            "user_id": user_id,
            "name": user_name,
            "username": user_username,
            "avatar_url": user_avatar_url,
            "registered_at": registered_at,
        })

        # FetchedInfo インスタンス作成
        return FetchedInfo(like, user, media_list)


if __name__ == "__main__":
    cache_path = Path("./cache/")
    load_paths: list[Path] = [p for p in cache_path.glob("*bluesky.json*")]
    if len(load_paths) == 0:
        pprint.pprint("Cache file is not exist.")
        exit(-1)
    load_path: Path = load_paths[-1]
    fetched_entry_list: list[dict] = orjson.loads(load_path.read_bytes()).get("result")
    fetched_entry_list = fetched_entry_list["feed"]
    for entry in fetched_entry_list[:3]:
        fetched_info = FetchedInfo.create(entry)
        pprint.pprint(fetched_info)
