from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from bluesky_crawler.db.base import Base
from bluesky_crawler.db.model import User


class UserDB(Base):
    def __init__(self, db_path: str = "bksy_db.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(User).all()
        session.close()
        return result

    def upsert(self, record: User | list[User] | list[dict]) -> list[int]:
        """upsert

        Args:
            record (User | list[User] | list[dict]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[User] = []
        match record:
            case User():
                record_list = [record]
            case [User(), *rest] if all([isinstance(r, User) for r in rest]):
                record_list = record
            case [dict(), *rest] if all([isinstance(r, dict) for r in rest]):
                record_list = [User.create(r) for r in record]
            case _:
                raise TypeError("record is invalid type.")

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = session.query(User).filter(and_(User.user_id == r.user_id)).with_for_update()
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                p.user_id = r.user_id
                p.name = r.name
                p.username = r.username
                p.avatar_url = r.avatar_url
                p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result
