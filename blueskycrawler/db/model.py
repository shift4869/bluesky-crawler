import re
from pathlib import Path
from typing import Self

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()


class Like(Base):
    """likeモデル
    [id] INTEGER NOT NULL UNIQUE,
    [post_id] TEXT NOT NULL UNIQUE,
    [user_id] TEXT NOT NULL,
    [url] TEXT NOT NULL,
    [text] TEXT,
    [created_at] TEXT NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Like"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(256), nullable=False, unique=True)
    user_id = Column(String(256), nullable=False)
    url = Column(String(256), nullable=False)
    text = Column(String(512))
    created_at = Column(String(256), nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(self, post_id: str, user_id: str, url: str, text: str, created_at: str, registered_at: str):
        # self.id = id
        self.post_id = post_id
        self.user_id = user_id
        self.url = url
        self.text = text
        self.created_at = created_at
        self.registered_at = registered_at

    @classmethod
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "post_id": post_id,
                "user_id": user_id,
                "url": url,
                "text": text,
                "created_at": created_at,
                "registered_at": registered_at,
            }:
                return Like(post_id, user_id, url, text, created_at, registered_at)
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<Like(post_id='{self.post_id}')>"

    def __eq__(self, other):
        return isinstance(other, Like) and other.post_id == self.post_id

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "user_id": self.user_id,
            "url": self.url,
            "text": self.text,
            "created_at": self.created_at,
            "registered_at": self.registered_at,
        }


class User(Base):
    """ユーザーモデル
    [id] INTEGER NOT NULL UNIQUE,
    [user_id] TEXT NOT NULL UNIQUE,
    [name] TEXT,
    [username] TEXT NOT NULL,
    [avatar_url] TEXT,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(256), nullable=False, unique=True)
    name = Column(String(256))
    username = Column(String(256), nullable=False)
    avatar_url = Column(String(512))
    registered_at = Column(String(256), nullable=False)

    def __init__(self, user_id: str, name: str, username: str, avatar_url: str, registered_at: str):
        # self.id = id
        self.user_id = user_id
        self.name = name
        self.username = username
        self.avatar_url = avatar_url
        self.registered_at = registered_at

    @classmethod
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "user_id": user_id,
                "name": name,
                "username": username,
                "avatar_url": avatar_url,
                "registered_at": registered_at,
            }:
                return User(user_id, name, username, avatar_url, registered_at)
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}')>"

    def __eq__(self, other):
        return isinstance(other, User) and other.user_id == self.user_id

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "registered_at": self.registered_at,
        }


class Media(Base):
    """メディアモデル
    [id] INTEGER NOT NULL UNIQUE,
    [post_id] TEXT NOT NULL,
    [media_id] TEXT NOT NULL UNIQUE,
    [username] TEXT NOT NULL,
    [alt_text] TEXT,
    [mime_type] TEXT NOT NULL,
    [size] INTEGER NOT NULL,
    [url] TEXT NOT NULL,
    [created_at] TEXT NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Media"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(256), nullable=False)
    media_id = Column(String(256), nullable=False, unique=True)
    username = Column(String(256), nullable=False)
    alt_text = Column(String(512))
    mime_type = Column(String(256), nullable=False)
    size = Column(Integer, nullable=False)
    url = Column(String(512), nullable=False)
    created_at = Column(String(256), nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(
        self,
        post_id: str,
        media_id: str,
        username: str,
        alt_text: str,
        mime_type: str,
        size: int,
        url: str,
        created_at: str,
        registered_at: str,
    ):
        # self.id = id
        self.post_id = post_id
        self.media_id = media_id
        self.username = username
        self.alt_text = alt_text
        self.mime_type = mime_type
        self.size = size
        self.url = url
        self.created_at = created_at
        self.registered_at = registered_at

    @classmethod
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "post_id": post_id,
                "media_id": media_id,
                "username": username,
                "alt_text": alt_text,
                "mime_type": mime_type,
                "size": size,
                "url": url,
                "created_at": created_at,
                "registered_at": registered_at,
            }:
                return Media(post_id, media_id, username, alt_text, mime_type, size, url, created_at, registered_at)
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<Media(media_id='{self.media_id}', post_id='{self.post_id}')>"

    def __eq__(self, other):
        return isinstance(other, Media) and other.media_id == self.media_id and other.post_id == self.post_id

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "media_id": self.media_id,
            "username": self.username,
            "alt_text": self.alt_text,
            "mime_type": self.mime_type,
            "size": self.size,
            "url": self.url,
            "created_at": self.created_at,
            "registered_at": self.registered_at,
        }

    def get_filename(self) -> str:
        ext = ""
        if re.search(r"^.*?@.+$", (ext1 := self.url)):
            ext = "." + ext1.split("@")[-1]
        elif re.search(r"^.+?/.+$", (ext2 := self.mime_type)):
            ext = "." + ext2.split("/")[1]
            if ext.startswith(".x-"):
                ext = "." + ext[3:]

        if not re.search(r"^\..+$", ext):
            raise ValueError("failed to get filename, invalid extension.")

        return f"{self.post_id}_{self.username}{ext}"


if __name__ == "__main__":
    test_db = Path("./test_DB.db")
    test_db.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{test_db.name}", echo=True)
    Base.metadata.create_all(engine)

    session = Session(engine)
    result = session.query(Media).all()

    session.close()
    # test_db.unlink(missing_ok=True)
