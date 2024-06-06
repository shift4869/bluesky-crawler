from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from bluesky_crawler.db.base import Base
from bluesky_crawler.db.model import Media


class MediaDB(Base):
    def __init__(self, db_path: str = "bksy_db.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Media).all()
        session.close()
        return result

    def upsert(self, record: Media | list[Media] | list[dict]) -> list[int]:
        """upsert

        Args:
            record (Media | list[dict] | list[Media]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[Media] = []
        match record:
            case Media():
                record_list = [record]
            case [Media(), *rest] if all([isinstance(r, Media) for r in rest]):
                record_list = record
            case [dict(), *rest] if all([isinstance(r, dict) for r in rest]):
                record_list = [Media.create(r) for r in record]
            case _:
                raise TypeError("record is invalid type.")

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = (
                    session.query(Media)
                    .filter(and_(Media.post_id == r.post_id, Media.media_id == r.media_id))
                    .with_for_update()
                )
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                p.post_id = r.post_id
                p.media_id = r.media_id
                p.alt_text = r.alt_text
                p.mime_type = r.mime_type
                p.size = r.size
                p.url = r.url
                p.created_at = r.created_at
                p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result
