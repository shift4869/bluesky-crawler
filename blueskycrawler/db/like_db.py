from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from blueskycrawler.db.base import Base
from blueskycrawler.db.model import Like


class LikeDB(Base):
    def __init__(self, db_path: str = "bksy_db.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Like).all()
        session.close()
        return result

    def upsert(self, record: Like | list[Like] | list[dict]) -> list[int]:
        """upsert

        Args:
            record (Like | list[Like] | list[dict]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[Like] = []
        match record:
            case Like():
                record_list = [record]
            case [Like(), *rest] if all([isinstance(r, Like) for r in rest]):
                record_list = record
            case [dict(), *rest] if all([isinstance(r, dict) for r in rest]):
                record_list = [Like.create(r) for r in record]
            case _:
                raise TypeError("record is invalid type.")

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = session.query(Like).filter(and_(Like.post_id == r.post_id)).with_for_update()
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                p.post_id = r.post_id
                p.user_id = r.user_id
                p.url = r.url
                p.text = r.text
                p.created_at = r.created_at
                p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result
